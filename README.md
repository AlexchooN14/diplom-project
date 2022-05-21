# <p align="center">Diploma project</p>

### <p align="center">Hello,<br>With currently being a 12<sup>th</sup> grader in [TUES](https://www.elsys-bg.org/), to complete my course of education I have to devise, create and defend a diploma project.</p>
<br></br>
#### 💧⚙️ In this repo I will realize my project - an autonomous irrigation system that will:
* Consist of both software and hardware parts which will work inseparably
* Maintain up to 256 zones of irrigation
* Periodically collect information about the parameters of its environment with the period itself being configurable
* Identify the needed amount of irrigation with an algorithm, including:
    * Soil moisture in the last 24h
    * Weather forecast for the upcoming 24h
    * Illumination in the environment in the last 24h
    * Temperature and humidity of air in the last 24h
* Enable configuration of zones have:
    * An individual schedule of irrigation
    * An individual algorithm, suitable for the zone
    * An individual debit of the water resource in the zone
* Provide information for its state, and the irrigation processes in every zone

#### 💻 Involved technologies with this project are:
* Flask - Python framework
* SQLAlchemy ORM
* PostgreSQL Database
* Micropython
* WPS
* MQTT

#### 📈 During my progress I will
- [ ] 💿 Create a database to store all data
- [ ] 📡 Realize an MQTT communication between the server and a potential device
- [ ] 🧮 Create an irrigation decision algorithm and test it with mock data
- [ ] 📟 Create the hardware device
- [ ] 🌐 Implement device's socket server in AP Wi-Fi mode for home internet data submit
- [ ] 📡 Test MQTT communication with the hardware device
- [ ] 🔎 Implement all topics from topic tree diagram, including all json files
- [ ] ✔️Create Automatic Tests
- [ ] 🌐 Create the REST API endpoints
- [ ] 📃 Describe everything done in a documentation file
