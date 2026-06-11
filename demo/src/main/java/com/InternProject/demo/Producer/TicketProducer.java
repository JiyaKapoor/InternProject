package com.InternProject.demo.Producer;

import com.InternProject.demo.model.Ticket;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

import static org.hibernate.query.sqm.tree.SqmNode.log;


@Service
public class TicketProducer {

    private static final String TOPIC = "tickets.raw";
    @Autowired
    private KafkaTemplate<String, Ticket> kafkaTemplate;


    public void sendTicket(Ticket ticket) {
        kafkaTemplate.send(TOPIC, ticket.getNumber(), ticket)
                .whenComplete((result, ex) -> {
                    if (ex != null) {
                        System.out.println("Failed to send ticket {}: {}"+ ticket.getNumber()+ex.getMessage());
                    } else {
                        System.out.println("Sent ticket"+ticket.getNumber()+"to partition"+result.getRecordMetadata().partition()+"offset"+result.getRecordMetadata().offset());
                    }
                });
    }
}