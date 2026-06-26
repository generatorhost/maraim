from maraim.kernel_v2.runtime_object import DNARuntime


class SampleModelRuntime(DNARuntime):
    def __init__(self):
        super().__init__(
            namespace="models.local",
            key="sample_model",
            version="1.0.0",
            kind="model",
            capabilities=["text_generation", "reasoning"],
            metadata={
                "format": "runtime",
                "note": "Sample model runtime proving model support without JSON/YAML/compiler.",
            },
        )

    def execute(self, payload=None):
        payload = payload or {}
        return {
            "ok": True,
            "model": self.id,
            "response": "Sample model runtime executed.",
            "input": payload,
        }
