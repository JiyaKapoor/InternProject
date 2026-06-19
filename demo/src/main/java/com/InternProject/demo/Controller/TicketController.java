package com.InternProject.demo.Controller;

import com.InternProject.demo.Service.EmailToTicketParser;
import com.InternProject.demo.model.Ticket;
import com.InternProject.demo.Producer.TicketProducer;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.Map;

@RestController
@RequestMapping("/api/emails")
public class TicketController {

    @Autowired
    private TicketProducer ticketProducer;
    @Autowired
    private EmailToTicketParser emailToTicketParser;
    @PostMapping
    public ResponseEntity<String> receiveEmail(@RequestBody Map<String, Object> emailData) {


        String to = (String) emailData.get("to");
        String subject = (String) emailData.get("subject");
        String body = (String) emailData.get("body");
        String from=(String) emailData.get("from");
        String receivedTime = (String) emailData.get("receivedTime");

        System.out.println("=== New Email Received ===");
        System.out.println("From: " + from);
        System.out.println("Subject: " + subject);
        System.out.println("Body: " + body);
        System.out.println("=========================");
        Ticket ticket=emailToTicketParser.parse(emailData);
        ticket.setUserEmail(from);

        ticketProducer.sendTicket(ticket);                

        System.out.println("Ticket created: " + ticket.getNumber());
        System.out.println("Short Desc: " + ticket.getShortDescription());
        return ResponseEntity.ok("received");
    }

    @GetMapping("/health")
    public String health() {
        return "OK";
    }
}