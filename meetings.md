# Meetings notes

## Meeting 1.
* **DATE:2024-01-29**
* **ASSISTANTS: Ivan Sanchez**

### Minutes
*Summary of what was discussed during the meeting*
The discussion of the meeting was about the 1st deliverable about the api description. How different our project needs to be compared to the exercises and what grade are we aiming for as a group.

### Action points
*List here the actions points discussed with assistants*
1) fix typos in the main concept and relation section.
2) update diagram to include multiple warehouses
3) extend the uses section to include other clients that could use the api and proivde more ideas on how te api could be used.
4) Mention the methods used in the related work section and try to find clearly the api of the related work mentioned or find new/more services to which we can see the api
5) look for clients(applications) who use the apis mentioned in related work



## Meeting 2.
* **DATE:2024-02-13**
* **ASSISTANTS: Ivan Sanchez**

### Minutes
*Summary of what was discussed during the meeting*
We discussed our database structure and details related to implementing the API for the next deadline. Ivan said that expressing data to the client is more important than the performance of the API. The database structure does not need to be the same as the API structure. 


### Action points
*List here the actions points discussed with assistants*
1) We could possibly implement Location as part of the Warehouse class. For example, Location doesn't use foreign keys.
2) We should validate the data either in the database or the API, but not both.
3) Check if backref works since it was not used in the exercise example
4) Change relationship between warehouse and items. It should not be direct. Change relationship diagram to match.
5) Can't have stock where item does not exist. This relationship should be fixed.
6) Primary key as a string could be a problem


## Meeting 3.
* **DATE:2024-03-21**
* **ASSISTANTS: Ivan Sanchez**

### Minutes
*Summary of what was discussed during the meeting*
We discussed how there were some inconsistencies from the wiki to the code in naming resources. We also needed to clarify that some of our resources point to the same location. Ivan also encouraged us to change from static yaml files to dynamic swaggering although the next deliverable due date was a few days away. He also mentioned that we should add in the final review how the Github Copilot extension was used while writing code.

### Action points
In wiki
1) Check consistency in resource table. 
2) Possibly reduce number of resources, many ways to look up item
3) Addressability - comment how a single resource can be accessed through different urls
4) Uniform interface - give example in description of how to add an item

Code structure - probably fine
1) Status500 error during testing - delete behavior needs to be fixed
2) Add multiple schemas for different methods - authentication


## Meeting 4.
* **DATE: 2024-04-09**
* **ASSISTANTS: Ivan Sanchez**

### Minutes
*Summary of what was discussed during the meeting*
The main points of this meeting covered our API diagram, documentation, and hypermedia implementation and testing. The testing coverage was good and Ivan mentioned it can count as extra work. The wiki was in good shape as well. 500 error during Stock PUT test and deserializer failed


### Action points
*List here the actions points discussed with assistants*
1) The link relations diagram should show entry points
2) Authentication is not discussed
3) Wiki should have instructions for how to view swaggering
4) Swaggering errors occured during demonstration
5) 500 errors should not be documented


## Midterm meeting
* **DATE:**
* **ASSISTANTS:**

### Minutes
*Summary of what was discussed during the meeting*

### Action points
*List here the actions points discussed with assistants*




## Final meeting
* **DATE:**
* **ASSISTANTS:**

### Minutes
*Summary of what was discussed during the meeting*

### Action points
*List here the actions points discussed with assistants*




