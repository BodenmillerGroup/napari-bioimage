import os
from typing import TYPE_CHECKING, Optional, Union

from napari.utils.events import EventedList
from napari.viewer import Viewer
from pluggy import PluginManager

from . import hookspecs
from ._exceptions import BioImageException
from .model import Image

if TYPE_CHECKING:
    from .widgets import QBioImageWidget

PathLike = Union[str, os.PathLike]


class BioImageController:
    def __init__(self) -> None:
        self._pm = PluginManager("napari-bioimage")
        self._pm.add_hookspecs(hookspecs)
        self._pm.load_setuptools_entrypoints("napari-bioimage")
        self._viewer: Optional[Viewer] = None
        self._widget: Optional["QBioImageWidget"] = None
        self._images: EventedList[Image] = EventedList(
            basetype=Image, lookup={str: lambda image: image.name}
        )

    def _get_reader_function(
        self, path: PathLike
    ) -> Optional[hookspecs.ReaderFunction]:
        reader_function = self._pm.hook.napari_bioimage_get_reader(path=path)
        return reader_function

    def _get_writer_function(
        self, path: PathLike, image: Image
    ) -> Optional[hookspecs.WriterFunction]:
        writer_function = self._pm.hook.napari_bioimage_get_writer(
            path=path, image=image
        )
        return writer_function

    def can_read(self, path: PathLike) -> bool:
        return self._get_reader_function(path) is not None

    def can_write(self, path: PathLike, image: Image) -> bool:
        return self._get_writer_function(path, image) is not None

    def read(self, path: PathLike) -> Image:
        reader_function = self._get_reader_function(path)
        if reader_function is None:
            raise BioImageControllerException(f"No reader found for {path}")
        try:
            image = reader_function(path)
        except Exception as e:
            raise BioImageControllerException(e)
        self._images.append(image)
        return image

    def write(self, path: PathLike, image: Image) -> None:
        writer_function = self._get_writer_function(path, image)
        if writer_function is None:
            raise BioImageControllerException(f"No writer found for {path}")
        try:
            writer_function(path, image)
        except Exception as e:
            raise BioImageControllerException(e)

    def register_viewer(self, viewer: Viewer) -> None:
        assert self._viewer is None
        self._viewer = viewer

    def register_widget(self, widget: "QBioImageWidget") -> None:
        assert self._widget is None
        self._widget = widget

    @property
    def pm(self) -> PluginManager:
        return self._pm

    @property
    def viewer(self) -> Optional[Viewer]:
        return self._viewer

    @property
    def widget(self) -> Optional["QBioImageWidget"]:
        return self._widget

    @property
    def images(self) -> EventedList[Image]:
        return self._images


class BioImageControllerException(BioImageException):
    pass


controller = BioImageController()
