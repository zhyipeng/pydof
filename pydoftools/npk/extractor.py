import base64
import io
import os
import typing
from pathlib import Path

from pydoftools.npk import IMGFactory, NPK


def extra_images(npk: NPK, out: os.PathLike):
    out = Path(out)
    if not out.exists():
        out.mkdir(parents=True)

    for file in npk.files:
        dirpath = out / file.name
        if not dirpath.exists():
            dirpath.mkdir(parents=True)

        img = IMGFactory.open(io.BytesIO(file.data))
        for i, _img in enumerate(img.images):
            pil_image = img.build(_img)
            with (dirpath / f'{i}.png').open('wb') as fp:
                pil_image.save(fp)


def extra_base64(npk: NPK) -> typing.Generator[str, None, None]:
    for file in npk.files:
        img = IMGFactory.open(io.BytesIO(file.data))
        for i, _img in enumerate(img.images):
            pil_img = img.build(_img)
            with io.BytesIO() as buf:
                pil_img.save(buf, format='png')
                b = buf.getvalue()

            yield base64.b64encode(b).decode()
