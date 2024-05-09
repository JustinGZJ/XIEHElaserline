import importlib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "20000 CNY"}


class FunctionCall(BaseModel):
    function_name: str
    module_path: str
    kwargs: dict


@app.post("/call-function/")
async def call_function(data: FunctionCall):
    # 动态调用本地python代
    try:
        # 替换路径中/或者\为.
        data.module_path = (data.module_path
                            .replace("/", ".")
                            .replace("\\", ".")
                            .replace(".py", ""))
        module = importlib.import_module(data.module_path)
        func = getattr(module, data.function_name)
        return func(**data.kwargs)
    except ModuleNotFoundError:
        raise HTTPException(status_code=404, detail="Module not found")
    except AttributeError:
        raise HTTPException(status_code=404, detail="Function not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
