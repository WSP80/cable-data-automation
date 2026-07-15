class GeneratorPipeline:
    """
    Generates manufacturer-specific cable designations from UCM.
    """

    def __init__(self, generators: dict):
        self.generators = generators

    def generate(self, ucm, target_manufacturer: str) -> str:
        if target_manufacturer not in self.generators:
            raise ValueError(
                f"No generator registered for manufacturer: {target_manufacturer}"
            )

        generator = self.generators[target_manufacturer]

        return generator.generate(ucm)