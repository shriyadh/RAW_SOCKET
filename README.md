# RAW SOCKET PROGRAMMING
Computer Networking - Project 4 <br>
Project by - Mariah Maynard and Shriya Dhaundiyal
<br>
<br>

## **HIGH LEVEL_APPROACH -- UNDERSTANDING PROJECT DESGIN**

In order to start this project, we needed an in-depth understanding of the OSI model and the role of each layer. 
This project required us to get familiar with low-level operations of the internet protocol stack. We had to go beyond implemeting application level protocols (HTTP GET/ RECEIVE) and build IP and TCP headers in each packet for sending and receicing data.

We based our understanding of the project on the following steps:

![image](https://user-images.githubusercontent.com/110204529/223234905-8aa8832b-09da-48c8-aa6f-6955c91509cd.png)

As the data flows down the different layers, each layer attaches a header to it. When a client program wants to connect to a server, it creates a GET request and passes it down to the TCP layer. The TCP layer creates a TCP packet with the TCP header and the GET request and passes it down to the IP layer. The IP layer further attaches its own header to the TCP segment and creates a IP Datagram ( IP HEADER + TCP HEADER + DATA ) and sends it down to the data link/ ethernet layer.

![image](https://user-images.githubusercontent.com/110204529/223235111-f7cedea4-3d6e-4dd2-b8ef-9a25460fcfe0.png)

Our program design for **SENDING** data is also based on the same network flow: **PACKING**

**APPLICATION LAYER ----> DATA**<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;        |<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;        |<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;        |<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;        |<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;        V<br>
**TCP LAYER ----> TCP SEGMENT ( DATA + TCP HEADER)**<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;       |<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;       |<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;       |<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;       |<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;       V<br>
**IP LAYER ----> IP DATAGRAM ( DATA + TCP HEADER + IP HEADER)**<br>

<br>
<br>

Our program design for **RECEIVING** data is also based on the same network flow: **UNPACKING**

**IP LAYER ----> IP DATAGRAM ( DATA + TCP HEADER + IP HEADER)**<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;        |<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;        |<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;        |<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;        |<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;        V<br>
**TCP LAYER ----> TCP SEGMENT ( DATA + TCP HEADER)**<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;        |<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;       |<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;       |<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;       |<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;       V<br>
**APPLICATION LAYER ----> DATA**<br>
<br>
<br>

#### **SHRIYA** <br>
Based off this understanding, I started with the basic structure of the TCP/IP pakcets. After setting up the ground functionality for parsing data from command line to getting an idea of how the first interaction on application level would be, the design decided was to have http -> tcp -> ip and backwards for receiving. I first laid out functions for packing and unpacking TCP packet which involved a lot of handling on ends like figuring out the appropriate port numbers and ip addresses for the local/remote servers and making sure the validated checksums were correct. Once that was down, it made sense to have a class TCP deal with all functionality at the TCP level. I used the rawhtttpget to create a TCP object within it and call on it to establish the three way handshake. After establishing the three way handshake and adding appropriate checks for timeout and checksums and making sure the right seq/ack numbers are handled, I implemented the connection teardown as it was very similar in logic to the previous process. Once Mariah implemented the receiving function for our program, I added functionality to control the congestion window, avoid duplicates and proper timeout and checksum errors for the same. In the end, since we decided to stick with HTTP 1.1, I implemented the chunk encoded functionality for pages with transfer encoding set to chunked. <br>
#### **CHALLENGES FACED**<br>
I think the most challenging part of this project was to come up with a good design for it. There was a lot of moving parts involved in this project and it was essential to have a good breakdown of what part of code is going to resonate with which layer. Understanding the structure of the packets and implementing the correct indices was also a challenge. We struggled a bit with checksum validation because of incorrect indexing. Handling the congestion window was extremely confusing becuase it was hard to see how it would affect the ongoing code and make it work according to the flow of the program was really tricky. It also took a lot of trials and errors to get our chunk encoded file to download correctly which I ultimately narrowed down to a problem with our GET request. Overall, I felt that this project was a step up from the previous projects and required a thorough run down of theoretical knowledge as well as good expertise in program design. 
<br>

#### **MARIAH** <br>

#### **CHALLENGES FACED**<br>


## **FEATURES IMPLEMENTED**
**BOTH**<br>
    
* Filter out incoming packets to only use the one needed <br><br>
    
**IP** <br>
* Validate the checksums of incoming packets  
* Set the correct version, header length and total length, protocol identifier, and checksum in each outgoing packet
* Set the source and destination IP in each outgoing packet
* Validate IP headers, checksum from the remote server. The protocol identifier matches the contents of the encapsulated header. <br><br>
    
 **TCP** <br>
* Verified the checksums of incoming TCP packets, and generated correct checksums for outgoing packets
* Selected a valid local port to send traffic on, perform the three-way handshake, and correctly handle connection teardown
* Correctly handled sequence and acknowledgement numbers. 
* Managed the advertised window as fit. 
* Implemented basic timeout functionality: if a packet is not ACKed within 1 minute, assume the packet is lost and retransmit it. 
* Able to receive out-of-order incoming packets and put them back into the correct order before delivering them to the higher-level, 
* HTTP handling
* Identify and discarded duplicate packets. 
* Implemented a basic congestion window: start with cwnd=1, and increment the cwnd after each succesful ACK, up to a fixed maximum of 1000 (e.g. cwnd must be             <=1000 at all times). If program observes a packet drop or a timeout, reset the cwnd to 1.  <br><br>
    


<br>
<br>


