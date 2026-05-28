from typing import Annotated

from fastapi import Depends

from bootstrap.i18n import i18n
from lib.i18n.translator import Translator

get_current_translator = i18n.get_dependency()

I18nDep = Annotated[Translator, Depends(get_current_translator)]
