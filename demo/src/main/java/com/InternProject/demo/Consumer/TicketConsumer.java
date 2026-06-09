package com.InternProject.demo.Consumer;

import com.InternProject.demo.model.Ticket;

import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;


@Service
public class TicketConsumer {

    @KafkaListener(topics = "tickets.raw", groupId = "ticket-processor")
    public void consume(Ticket ticket) {
        System.out.print("Received ticket: [{}] | Priority: {} | State: {} | Assigned to: {}"+
                ticket.getNumber()+
                ticket.getPriority()+
                ticket.getState()+
                ticket.getAssignedTo());

        // This is where the ML classifier call will go later
    }
}