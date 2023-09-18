from __future__ import annotations

import os
import gc

from contextlib import contextmanager
from typing import Iterator, Any, Optional, TYPE_CHECKING
from typing_extensions import Self

if TYPE_CHECKING:
    from PIL.Image import Image
    import torch

class SupportModelImageProcessor:
    def __init__(self, **kwargs: Any) -> None:
        """
        Provides a base class for processing images with an AI model.
        """
        self.kwargs = kwargs

    def __enter__(self) -> Self:
        """
        Compatibility with contexts
        """
        return self

    def __exit__(self, *args: Any) -> None:
        """
        Compatibility with contexts
        """
        return

    def __call__(self, image: Image) -> Image:
        """
        Implemented by the image processor.
        """
        raise NotImplementedError("Implementation did not override __call__")

class SupportModel:
    """
    Provides a base class for AI models that support diffusion.
    """

    process: Optional[SupportModelImageProcessor] = None

    def __init__(self, model_dir: str, device: torch.device, dtype: torch.dtype) -> None:
        if model_dir.startswith("~"):
            model_dir = os.path.expanduser(model_dir)
        self.model_dir = model_dir
        self.device = device
        self.dtype = dtype

    @classmethod
    def get_default_instance(cls) -> SupportModel:
        """
        Builds a default interpolator without a configuration passed
        """
        import torch
        from enfugue.diffusion.util import get_optimal_device
        from enfugue.util import get_local_configuration
        device = get_optimal_device()
        try:
            configuration = get_local_configuration()
        except:
            from pibble.api.configuration import APIConfiguration
            configuration = APIConfiguration()

        return cls(
            configuration.get("enfugue.engine.cache", "~/.cache/enfugue/other"),
            device,
            torch.float16 if device.type == "cuda" else torch.float32
        )

    @contextmanager
    def context(self) -> Iterator[Self]:
        """
        Cleans torch memory after processing.
        """
        self.loaded = True
        yield self
        self.loaded = False
        if getattr(self, "process", None) is not None:
            del self.process
        if self.device.type == "cuda":
            import torch
            import torch.cuda

            torch.cuda.empty_cache()
        elif self.device.type == "mps":
            import torch
            import torch.mps

            torch.mps.empty_cache()
        gc.collect()
