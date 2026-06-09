package com.InternProject.demo.Controller;

import com.InternProject.demo.model.Ticket;
import com.InternProject.demo.Producer.TicketProducer;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/tickets")
@RequiredArgsConstructor
public class TicketController {

    private final TicketProducer ticketProducer;

    @PostMapping
    public ResponseEntity<String> createTicket(@RequestBody Ticket ticket) {
        ticketProducer.sendTicket(ticket);
        return ResponseEntity.accepted().body("Ticket " + ticket.getNumber() + " queued for processing");
    }
}