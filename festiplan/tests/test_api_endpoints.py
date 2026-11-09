from app.config import settings

DAY="2027-06-18"

def _post(client,url,payload):
 r=client.post(url,json=payload)
 assert r.status_code==201,r.text
 return r.json()

def _setup(client):
 festival=_post(client,"/festivals",{"name":"Test Fest","location":"Clisson","start_date":f"{DAY}T10:00:00","end_date":"2027-06-20T23:59:00"})
 stage=_post(client,"/stages",{"festival_id":festival["id"],"name":"Main","capacity":1000,"available_equipment":["lights"]})
 artist_a=_post(client,"/artists",{"name":"Artist A","genre":"Metal","required_equipment":["lights"]})
 artist_b=_post(client,"/artists",{"name":"Artist B","genre":"Metal","required_equipment":[]})
 return festival,stage,artist_a,artist_b

def _concert_payload(festival,artist,stage,start,end):
 return {"festival_id":festival["id"],"artist_id":artist["id"],"stage_id":stage["id"],
         "start_time":f"{DAY}T{start}","end_time":f"{DAY}T{end}"}

def test_schedule_concert_and_list_it_chronologically(client):
 festival,stage,a,b=_setup(client)
 late=_post(client,"/concerts",_concert_payload(festival,b,stage,"21:00:00","22:00:00"))
 early=_post(client,"/concerts",_concert_payload(festival,a,stage,"18:00:00","19:00:00"))
 r=client.get(f"/concerts/schedule/{festival['id']}")
 assert [c["id"] for c in r.json()]==[early["id"],late["id"]]
 assert [c["id"] for c in client.get("/concerts",params={"festival_id":festival["id"]}).json()]==[early["id"],late["id"]]

def test_schedule_overlapping_concert_is_rejected(client):
 festival,stage,a,b=_setup(client)
 _post(client,"/concerts",_concert_payload(festival,a,stage,"18:00:00","19:00:00"))
 r=client.post("/concerts",json=_concert_payload(festival,b,stage,"18:30:00","19:30:00"))
 assert r.status_code==400

def test_schedule_with_missing_equipment_is_rejected(client):
 festival,_,a,_=_setup(client)
 bare=_post(client,"/stages",{"festival_id":festival["id"],"name":"Bare","capacity":10,"available_equipment":[]})
 r=client.post("/concerts",json=_concert_payload(festival,a,bare,"18:00:00","19:00:00"))
 assert r.status_code==400

def test_schedule_outside_festival_is_rejected(client):
 festival,stage,a,_=_setup(client)
 r=client.post("/concerts",json={**_concert_payload(festival,a,stage,"18:00:00","19:00:00"),"start_time":"2027-06-01T18:00:00","end_time":"2027-06-01T19:00:00"})
 assert r.status_code==400

def test_schedule_with_unknown_festival_is_rejected(client):
 festival,stage,a,_=_setup(client)
 r=client.post("/concerts",json={**_concert_payload(festival,a,stage,"18:00:00","19:00:00"),"festival_id":999})
 assert r.status_code==400

def test_unknown_concert_returns_404(client):
 assert client.get("/concerts/999").status_code==404
 assert client.post("/concerts/999/cancel").status_code==404
 assert client.patch("/concerts/999/reschedule",json={"start_time":f"{DAY}T18:00:00","end_time":f"{DAY}T19:00:00"}).status_code==404

def test_cancel_concert_removes_it_from_the_schedule(client):
 festival,stage,a,_=_setup(client)
 concert=_post(client,"/concerts",_concert_payload(festival,a,stage,"18:00:00","19:00:00"))
 r=client.post(f"/concerts/{concert['id']}/cancel")
 assert r.status_code==200 and r.json()["status"]=="cancelled"
 assert client.get(f"/concerts/schedule/{festival['id']}").json()==[]

def test_cancelled_concert_cannot_be_rescheduled(client):
 festival,stage,a,_=_setup(client)
 concert=_post(client,"/concerts",_concert_payload(festival,a,stage,"18:00:00","19:00:00"))
 client.post(f"/concerts/{concert['id']}/cancel")
 r=client.patch(f"/concerts/{concert['id']}/reschedule",json={"start_time":f"{DAY}T20:00:00","end_time":f"{DAY}T21:00:00"})
 assert r.status_code==409

def test_reschedule_with_invalid_slot_is_rejected(client):
 festival,stage,a,_=_setup(client)
 concert=_post(client,"/concerts",_concert_payload(festival,a,stage,"18:00:00","19:00:00"))
 r=client.patch(f"/concerts/{concert['id']}/reschedule",json={"start_time":f"{DAY}T21:00:00","end_time":f"{DAY}T20:00:00"})
 assert r.status_code==400

def test_published_planning_lifecycle(client):
 festival,stage,a,b=_setup(client)
 concert=_post(client,"/concerts",_concert_payload(festival,a,stage,"18:00:00","19:00:00"))
 fid=festival["id"]
 published=client.post(f"/festivals/{fid}/publish")
 assert published.status_code==200 and published.json()["status"]=="published"
 assert client.post(f"/festivals/{fid}/publish").status_code==409
 assert client.post("/concerts",json=_concert_payload(festival,b,stage,"20:00:00","21:00:00")).status_code==409
 assert client.post(f"/concerts/{concert['id']}/cancel").status_code==409
 reopened=client.post(f"/festivals/{fid}/unpublish")
 assert reopened.status_code==200 and reopened.json()["status"]=="preparation"
 assert client.post("/concerts",json=_concert_payload(festival,b,stage,"20:00:00","21:00:00")).status_code==201

def test_unpublish_requires_a_published_planning(client):
 festival,_,_,_=_setup(client)
 assert client.post(f"/festivals/{festival['id']}/unpublish").status_code==409

def test_publish_unknown_festival_returns_404_and_unpublish_too(client):
 assert client.post("/festivals/999/publish").status_code==404
 assert client.post("/festivals/999/unpublish").status_code==404

def test_publish_succeeds_even_if_notification_fails(client,monkeypatch):
 festival,_,_,_=_setup(client)
 monkeypatch.setattr(settings,"fail_notifications",True)
 r=client.post(f"/festivals/{festival['id']}/publish")
 assert r.status_code==200
 assert client.get("/festivals").json()[0]["status"]=="published"

def test_cancel_succeeds_even_if_notification_fails(client,monkeypatch):
 festival,stage,a,_=_setup(client)
 concert=_post(client,"/concerts",_concert_payload(festival,a,stage,"18:00:00","19:00:00"))
 monkeypatch.setattr(settings,"fail_notifications",True)
 assert client.post(f"/concerts/{concert['id']}/cancel").status_code==200

def test_report_and_list_incidents(client):
 festival,stage,a,_=_setup(client)
 concert=_post(client,"/concerts",_concert_payload(festival,a,stage,"18:00:00","19:00:00"))
 first=_post(client,"/incidents",{"concert_id":concert["id"],"description":"Panne de courant","occurred_at":f"{DAY}T18:10:00"})
 second=_post(client,"/incidents",{"concert_id":concert["id"],"description":"Retard","occurred_at":f"{DAY}T18:20:00"})
 assert first["resolved"] is False
 listed=client.get("/incidents",params={"concert_id":concert["id"]}).json()
 assert [i["id"] for i in listed]==[second["id"],first["id"]]

def test_incident_without_occurred_at_gets_a_date(client):
 festival,stage,a,_=_setup(client)
 concert=_post(client,"/concerts",_concert_payload(festival,a,stage,"18:00:00","19:00:00"))
 assert _post(client,"/incidents",{"concert_id":concert["id"],"description":"Panne"})["occurred_at"]

def test_incident_with_blank_description_is_rejected(client):
 festival,stage,a,_=_setup(client)
 concert=_post(client,"/concerts",_concert_payload(festival,a,stage,"18:00:00","19:00:00"))
 assert client.post("/incidents",json={"concert_id":concert["id"],"description":"     "}).status_code==400
 assert client.get("/incidents").json()==[]

def test_incident_for_unknown_concert_returns_404(client):
 assert client.post("/incidents",json={"concert_id":999,"description":"Panne"}).status_code==404

def test_stage_for_unknown_festival_is_rejected(client):
 r=client.post("/stages",json={"festival_id":999,"name":"Main","capacity":10,"available_equipment":[]})
 assert r.status_code==400

def test_stage_and_artist_equipment_round_trip(client):
 festival,stage,a,_=_setup(client)
 assert client.get("/stages",params={"festival_id":festival["id"]}).json()[0]["available_equipment"]==["lights"]
 assert [x["required_equipment"] for x in client.get("/artists").json()]==[["lights"],[]]
