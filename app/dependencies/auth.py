from typing import Annotated

from fastapi import Depends

from lib.auth import AuthUserMixin, get_backend, make_auth_dependency

get_current_user = make_auth_dependency(get_backend())
get_current_user_safe = make_auth_dependency(get_backend(), raise_exception=False)

AuthDep = Annotated[AuthUserMixin, Depends(get_current_user)]
AuthSafeDep = Annotated[AuthUserMixin | None, Depends(get_current_user_safe)]
