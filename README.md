# RUN SERVER
`uvicorn app.main:app --port 8484 --host 0.0.0.0`

# run curl
`curl -v -X PUT -H "Content-Type: application/json" \ -d '{"note_path": "haha.txt", "note_value": "RODION"}' \ "http://0.0.0.0:8484/apiv1/update-note"`
