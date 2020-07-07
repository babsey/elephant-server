import neo
import quantities as pq


class Units:
    def __init__(self, time="ms", amplitude="mV", rate="Hz"):
        self.time = pq.Quantity(1, units=time)
        self.amplitude = pq.Quantity(1, units=amplitude)
        self.rate = pq.Quantity(1, units=rate)

    @property
    def units_all(self):
        return self.time, self.amplitude, self.rate

    def rescale(self, quantity: pq.Quantity):
        if not isinstance(quantity, pq.Quantity):
            raise TypeError(f"Expected Quantity, got '{type(quantity)}'")
        dimensionality = quantity.dimensionality.simplified
        for reference in self.units_all:
            if reference.dimensionality.simplified == dimensionality:
                return quantity.rescale(reference)
        raise ValueError(f"Unknown units: '{quantity.units}'")


class Deserializer:

    def __init__(self, units: Units, t_start=None, t_stop=None,
                 sampling_rate=None):
        self.units = units
        self.t_start = t_start
        self.t_stop = t_stop
        self.sampling_rate = sampling_rate

    def to_spiketrains(self, data_list):
        return [self.to_spiketrain(data) for data in data_list]

    def to_analog_signals(self, data_list):
        return [self.to_analog_signal(data) for data in data_list]

    def to_spiketrain(self, data):
        if not isinstance(data, dict):
            data = dict(times=data, units=self.units.time, t_stop=self.t_stop,
                        t_start=self.t_start)
        return neo.SpikeTrain(**data)

    def to_analog_signal(self, data):
        if not isinstance(data, dict):
            data = dict(signal=data, units=self.units.amplitude,
                        sampling_rate=self.sampling_rate, t_start=self.t_start)
        else:
            data = data.copy()
            data.setdefault('units', self.units.amplitude)
            data.setdefault('sampling_rate', self.sampling_rate)
        return neo.AnalogSignal(**data)


def serialize(result, units: Units):
    if isinstance(result, dict):
        return {
            key: serialize(value, units=units) for key, value in result.items()
        }
    if isinstance(result, (list, tuple)):
        return [serialize(item, units=units) for item in result]
    if isinstance(result, neo.SpikeTrain):
        spiketrain = dict(times=serialize(result.times, units=units),
                          units=units.time,
                          t_stop=serialize(result.t_stop, units=units),
                          t_start=serialize(result.t_start, units=units))
        return dict(spiketrain=spiketrain)
    if isinstance(result, neo.AnalogSignal):
        signal = dict(signal=serialize(result.signal, units=units),
                      units=units.amplitude,
                      sampling_rate=serialize(result.sampling_rate,
                                              units=units),
                      t_start=serialize(result.t_start, units=units))
        return dict(signal=signal)
    if isinstance(result, pq.Quantity):
        return units.rescale(result).data.tolist()
    return result


def deserialize(json_data: dict):
    data_payload = json_data.get("data", {})

    # the output of nest has predefined units: ms, mV
    units_dict = json_data.get("units", {})
    units = Units(**units_dict)

    t_start = json_data.get("t_start", 0) * units.time
    t_stop = json_data.get("t_stop")
    sampling_rate = json_data.get("sampling_rate")
    converter = Deserializer(units=units, t_start=t_start, t_stop=t_stop,
                             sampling_rate=sampling_rate)

    data_neo = {}
    for key, value in data_payload.items():
        if key == 'signal':
            data_neo[key] = converter.to_analog_signal(value)
        elif key == 'signals':
            data_neo[key] = converter.to_analog_signals(value)
        if key == 'spiketrain':
            data_neo[key] = converter.to_spiketrain(value)
        elif key == 'spiketrains':
            data_neo[key] = converter.to_spiketrains(value)
        elif key in ['binsize', 't_start', 't_stop', 'times']:
            # time related units
            data_neo[key] = pq.Quantity(value, units=units.time)
        else:
            data_neo[key] = value

    return data_neo
