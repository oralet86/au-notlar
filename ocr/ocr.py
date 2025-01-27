from global_variables import logger, PROCESSOR_NAME, MODEL_NAME
from transformers import TrOCRProcessor, VisionEncoderDecoderModel


class ModelSingleton:
    """
    A singleton pair of a model and a processor.
    Use get_processor() to get the instantiated processor,
    Use get_model() to get the instantiated model.
    """

    _processor = None
    _model = None
    _processor_loaded = False
    _model_loaded = False

    @classmethod
    def get_processor(cls):
        logger.info("Processor requested!")
        if cls._processor is None:
            cls._processor = TrOCRProcessor.from_pretrained(PROCESSOR_NAME)
            cls._processor_loaded = True
        return cls._processor

    @classmethod
    def get_model(cls):
        logger.info("Model requested!")
        if cls._model is None:
            cls._model = VisionEncoderDecoderModel.from_pretrained(MODEL_NAME)
            cls._model_loaded = True
        return cls._model

    @classmethod
    def is_loaded(cls):
        return cls._processor_loaded and cls._model_loaded
