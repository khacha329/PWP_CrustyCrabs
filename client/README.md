Install the following package:

```
pip install windows-curses
``` 
 To test the app, type the following commands in cmd from the client folder of the project /PWP_CrustyCrabs/client/
 
 (NOTE: Ensure terminal window size is at least 80 x 25)

```
python client.py
```
This will display the handheld client menu in the terminal which you can then navigate using up and down arrow keys and select options using the enter key.

If the API database was initialized as described in the inventorymanager readme, then the existing items in the database can be queried using the interactive flask-shell or by viewing the local host address + /api/stocks/