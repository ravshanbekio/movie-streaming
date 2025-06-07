from starlette.responses import JSONResponse

class CreatedResponse(JSONResponse):
    def __init__(self, detail: str = "Ma'lumot muvaffaqiyatli yaratildi", status_code: int = 201):
        content = {"detail": detail}
        super().__init__(content=content, status_code=status_code)

class UpdatedResponse(JSONResponse):
    def __init__(self, detail: str = "Ma'lumot muvaffaqiyatli o'zgartirildi", status_code: int = 200):
        content = {"detail": detail}
        super().__init__(content=content, status_code=status_code)

class DeletedResponse(JSONResponse):
    def __init__(self, detail: str = "Ma'lumot muvaffaqiyatli o'chirildi", status_code: int = 200):
        content = {"detail": detail}
        super().__init__(content=content, status_code=status_code)

class NotFoundResponse(JSONResponse):
    def __init__(self, detail: str = "So'ralgan ma'lumot topilmadi", status_code: int = 400):
        content = {"detail": detail}
        super().__init__(content=content, status_code=status_code)

class CustomResponse(JSONResponse):
    def __init__(self, detail: str = None, status_code: int = 0):
        content = {"detail": detail}
        super().__init__(content=content, status_code=status_code)