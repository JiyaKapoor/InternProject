package com.InternProject.demo.Controller;

import com.InternProject.demo.model.Ticket;
import com.InternProject.demo.Producer.TicketProducer;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/tickets")
public class TicketController {
    @Autowired
    private TicketProducer ticketProducer;
    @PostMapping
    public ResponseEntity<String> receive(
            @RequestBody(required = false) String body,
            @RequestParam(required = false) String validationToken
    ) {

        // STEP 1: Microsoft webhook validation (MANDATORY)
        if (validationToken != null) {
            return ResponseEntity.ok(validationToken);
        }

        // STEP 2: Log incoming event
        System.out.println("📩 Outlook webhook received: " + body);

        // STEP 3: push to Kafka
        Ticket ticket = new Ticket();
        ticket.setShortDescription(body);

        ticketProducer.sendTicket(ticket);

        return ResponseEntity.ok("processed");

    }
}