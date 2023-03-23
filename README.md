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

#### **SHRIYA** <br><br>
Based off this understanding, I started with the basic structure of the TCP/IP pakcets. After setting up the ground functionality for parsing data from command line to getting an idea of how the first interaction on application level would be, the design decided was to have http -> tcp -> ip and backwards for receiving. I first laid out functions for packing and unpacking TCP packet which involved a lot of handling on ends like figuring out the appropriate port numbers and ip addresses for the local/remote servers and making sure the validated checksums were correct. Once that was down, it made sense to have a class TCP deal with all functionality at the TCP level. I used the rawhtttpget to create a TCP object within it and call on it to establish the three way handshake. After establishing the three way handshake and adding appropriate checks for timeout and checksums and making sure the right seq/ack numbers are handled, I implemented the connection teardown as it was very similar in logic to the previous process. Once Mariah implemented the receiving function for our program, I added functionality to control the congestion window, avoid duplicates, filtering out packets and proper timeout and checksum errors for the same. In the end, since we decided to stick with HTTP 1.1, I implemented the chunk encoded functionality for pages with transfer encoding set to chunked. <br><br>
#### **CHALLENGES FACED**<br><br>
I think the most challenging part of this project was to come up with a good design for it. There was a lot of moving parts involved in this project and it was essential to have a good breakdown of what part of code is going to resonate with which layer. Understanding the structure of the packets and implementing the correct indices was also a challenge. We struggled a bit with checksum validation because of incorrect indexing. Handling the congestion window was extremely confusing becuase it was hard to see how it would affect the ongoing code and make it work according to the flow of the program was really tricky. It also took a lot of trials and errors to get our chunk encoded file to download correctly which I ultimately narrowed down to a problem with our GET request. Overall, I felt that this project was a step up from the previous projects and required a thorough run down of theoretical knowledge as well as good expertise in program design. 
<br><br>

#### **MARIAH** <br><br>
I started with implementing the IP classes. This included creating receiving and sending functions, as adding the IP header would be the last step before sending our packect and removing it would be the first step when receiving our packet. This meant that I would need to add the sockets for receving and sending within this class as well. The receiving and sending functions were realtively simple to implement, and were followed by implementation of the packing and unpacking. For the packing function, I needed to research the necessary fields of the IP header to know which were necessary for our structs and how to index the correct fields. After the handshake was established, I then worked on sending the get request, receiving the data in packets, storing the file name/data and writing to file. Receving the packets took some time to implement. Because we had to handle out-of-order packets, I thought of different ways we could do this, and ultimately settled on using a priority queue. In this way, I was able to constantly receive the packets in a loop and add them to the priority queue. By also tracking the next expected sequence number, I could loop through the queue and send ACKs for the now in-order packets and add the data to a byte array. I also monitored the flags on the packets we received, and used the prescence of a fin flag to begin teardown or the absence of a fin flag to send a response ACK. Once this was implemented, I created the method for retreiving the server name/file name and the writing to file method. I used url parsing to obtain the necessary names and store them as variables. The writing method split the header from the body to check for error status. It then created and wrote to the file.
<br><br>
#### **CHALLENGES FACED**<br><br>
There were a few challenged faced, most of which I came into contact with when receiving data. Throughout the project we knew our sent checksum value was correct, but checking received checksums proved difficult. I needed the packet lengths to update the next expected sequence number and was not getting it from the TCP unpacking. It took some print statments to find out that there was an incorrect field, and therefore the length used for checking the checksum was also incorrect. There was also some difficulty in finding where to place the 3 minute timeout feature. At first, I placed it in the IP class but began to receive RSTs. I then moved it to the TCP class and refactored the part of the code with the 1 minute timeout feature to include 3 minutes for the socket itself. There was also some trouble with the amount of time our code took to download. The 50MB was taking a large amount of time. I tried to change the implementation of receiving data but nothing fixed the problem. It wasn't until I changed the way we were storing our received data to a bytearray that the files began to download quickly and we were pleased with the time it took. 

<br><br>

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


