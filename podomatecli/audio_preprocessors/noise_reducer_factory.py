from audio_preprocessors.logmsse_noise_reducer import LogMSSENoiseReducer
from audio_preprocessors.onestepweiner_noise_reducer import OneStepWeinerNoiseReducer
from audio_preprocessors.sox_noise_reducer import SoxNoiseReducer
from audio_preprocessors.twostepweiner_noise_reducer import TwoStepWeinerNoiseReducer


class NoiseReducerFactory(object):
    """
    Constructs NoiseReduction algorithms
    """

    ALGORITHMS = {
        LogMSSENoiseReducer.ID: LogMSSENoiseReducer,
        SoxNoiseReducer.ID: SoxNoiseReducer,
        OneStepWeinerNoiseReducer.ID: OneStepWeinerNoiseReducer,
        TwoStepWeinerNoiseReducer.ID: TwoStepWeinerNoiseReducer
    }

    @staticmethod
    def construct_noise_reducer(algorithm_id, params):
        if algorithm_id not in NoiseReducerFactory.ALGORITHMS:
            raise NotImplementedError("Unknown noise reduction algorithm: %s" % algorithm_id)

        return NoiseReducerFactory.ALGORITHMS[algorithm_id](
            window_size=4096, hop_size=2048, **params
        )
