import os,tempfile
import pytest
_tmp=tempfile.NamedTemporaryFile(suffix=".db",delete=False); _tmp.close()
os.environ["FESTIPLAN_DATABASE_URL"]=f"sqlite:///{_tmp.name}"

@pytest.fixture(scope="session")
def prepare():
 from app.adapters.outbound.persistence.database import Base,engine
 from app.adapters.outbound.persistence import models
 Base.metadata.create_all(bind=engine)
 yield
 Base.metadata.drop_all(bind=engine)
 try:
   os.unlink(_tmp.name)
 except OSError:
   pass

@pytest.fixture()
def client(prepare):
 from fastapi.testclient import TestClient
 from app.adapters.outbound.persistence.database import Base,SessionLocal
 from app.main import app
 db=SessionLocal()
 for table in reversed(Base.metadata.sorted_tables):
   db.execute(table.delete())
 db.commit(); db.close()
 with TestClient(app) as c:
   yield c
