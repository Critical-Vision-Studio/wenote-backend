# Wenote API
### Installing 
`git clone https://github.com/Critical-Vision-Studio/wenote-backend.git`

`cd wenote-backend`

### Running
`make`

### Testing
`make test`

### building
if you want just to build, run:
`make build`

### For Debug
```
GET-NOTE:
curl "http://127.0.0.1:8080/apiv1/get-note?note_path=haha.txt&branch_name=master"

GET-NOTE-NAMES:
curl "http://127.0.0.1:8080/apiv1/get-note?note_path=haha.txt&branch_name=master"

CREATE-NOTE
curl -v -X POST -H "Content-Type: application/json" -d '{"note_path": "haha.txt", "note_value": "RODION"}' "http://127.0.0.1:8080/apiv1/create-note"

UPDATE-NOTE:
curl -v -X PUT -H "Content-Type: application/json" -d '{"commit_id": "ea2b12b1bf9ed84c49fdc91376fe1206dbe68050", "branch_name": "master", "note_path": "haha.txt", "note_value": "RODION"}' "http://127.0.0.1:8080/apiv1/update-note"

DELETE-NOTE
curl -v -X DELETE -H "Content-Type: application/json" -d '{"note_path": "ee.txt", "branch_name": "master"}' "http://127.0.0.1:8080/apiv1/delete-note"
```
