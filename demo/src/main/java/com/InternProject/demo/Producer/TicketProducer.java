package com.InternProject.demo.Producer;

import com.InternProject.demo.model.Ticket;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class TicketProducer {

    private static final String TOPIC = "tickets.raw";
    private final KafkaTemplate<String, Ticket> kafkaTemplate;

    public void sendTicket(Ticket ticket) {
        kafkaTemplate.send(TOPIC, ticket.getNumber(), ticket)
                .whenComplete((result, ex) -> {
                    if (ex != null) {
                        log.error("Failed to send ticket {}: {}", ticket.getNumber(), ex.getMessage());
                    } else {
                        log.info("Sent ticket {} to partition {} offset {}",
                                ticket.getNumber(),
                                result.getRecordMetadata().partition(),
                                result.getRecordMetadata().offset());
                    }
                });
    }
}