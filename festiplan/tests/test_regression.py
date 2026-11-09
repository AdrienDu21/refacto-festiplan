from app.config import settings

DAY="2027-06-18"

def _post(client,url,payload):
 r=client.post(url,json=payload)
 assert r.status_code==201,r.text
 return r.json()

def _concert(client,festival,artist,stage,start,end):
 return _post(client,"/concerts",{
  "festival_id":festival["id"],"artist_id":artist["id"],"stage_id":stage["id"],
  "start_time":f"{DAY}T{start}","end_time":f"{DAY}T{end}"})

def _reschedule(client,concert_id,start,end):
 return client.patch(f"/concerts/{concert_id}/reschedule",
                     json={"start_time":f"{DAY}T{start}","end_time":f"{DAY}T{end}"})

def _get(client,concert_id):
 return client.get(f"/concerts/{concert_id}").json()

def _setup(client):
 festival=_post(client,"/festivals",{"name":"Test Fest","location":"Clisson","start_date":f"{DAY}T10:00:00","end_date":"2027-06-20T23:59:00"})
 stage1=_post(client,"/stages",{"festival_id":festival["id"],"name":"Main","capacity":1000,"available_equipment":[]})
 stage2=_post(client,"/stages",{"festival_id":festival["id"],"name":"Side","capacity":500,"available_equipment":[]})
 artist_a=_post(client,"/artists",{"name":"Artist A","genre":"Metal","required_equipment":[]})
 artist_b=_post(client,"/artists",{"name":"Artist B","genre":"Metal","required_equipment":[]})
 c1=_concert(client,festival,artist_a,stage1,"18:00:00","19:00:00")
 c2=_concert(client,festival,artist_b,stage1,"19:30:00","20:30:00")
 c3=_concert(client,festival,artist_b,stage2,"21:00:00","22:00:00")
 return {"festival":festival,"c1":c1,"c2":c2,"c3":c3}

def test_reschedule_overlapping_same_stage_is_rejected(client):
 d=_setup(client)
 r=_reschedule(client,d["c2"]["id"],"18:30:00","19:30:00")
 assert r.status_code==400
 assert _get(client,d["c2"]["id"])["start_time"]==d["c2"]["start_time"]

def test_reschedule_same_artist_on_two_stages_is_rejected(client):
 d=_setup(client)
 r=_reschedule(client,d["c3"]["id"],"20:00:00","21:00:00")
 assert r.status_code==400
 assert _get(client,d["c3"]["id"])["start_time"]==d["c3"]["start_time"]

def test_reschedule_to_free_slot_is_accepted(client):
 d=_setup(client)
 r=_reschedule(client,d["c2"]["id"],"20:00:00","21:00:00")
 assert r.status_code==200
 assert r.json()["start_time"]==f"{DAY}T20:00:00"

def test_reschedule_succeeds_even_if_notification_fails(client,monkeypatch):
 d=_setup(client)
 monkeypatch.setattr(settings,"fail_notifications",True)
 r=_reschedule(client,d["c2"]["id"],"20:00:00","21:00:00")
 assert r.status_code==200
 assert _get(client,d["c2"]["id"])["start_time"]==f"{DAY}T20:00:00"

def test_reschedule_after_publication_is_rejected(client):
 d=_setup(client)
 assert client.post(f"/festivals/{d['festival']['id']}/publish").status_code==200
 r=_reschedule(client,d["c2"]["id"],"20:00:00","21:00:00")
 assert r.status_code in (400,409)
 assert _get(client,d["c2"]["id"])["start_time"]==d["c2"]["start_time"]
