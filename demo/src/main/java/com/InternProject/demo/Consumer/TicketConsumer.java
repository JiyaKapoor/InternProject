package com.InternProject.demo.Consumer;

import com.InternProject.demo.Repository.TicketRepository;
import com.InternProject.demo.model.Ticket;

import com.InternProject.demo.model.TicketState;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;


@Service

public class TicketConsumer {

    private final RestTemplate restTemplate = new RestTemplate();
    private static final String FASTAPI_URL = "http://localhost:8000/analyze";
    @Autowired
    TicketRepository ticketRepository;
    @KafkaListener(topics = "tickets.raw", groupId = "ticket-processor")
    public void consume(Ticket ticket) {
        System.out.println("Received ticket: " + ticket.getNumber() +
                " | Priority: " + ticket.getPriority() +
                " | State: " + ticket.getState() +
                " | Assigned to: " + ticket.getAssignedTo());

        // Build request to FastAPI
        Map<String, Object> request = new HashMap<>();
        request.put("ticket_number", ticket.getNumber());
        request.put("short_description", ticket.getShortDescription());

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(request, headers);

        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(
                    FASTAPI_URL, entity, Map.class
            );
            ticket.setResolvedAt(LocalDateTime.now());
            ticket.setResolution(response.getBody().get("answer").toString());
            if(LocalDateTime.now().isAfter(ticket.getSLADue()))ticket.setSLA_Breached(true);
            else ticket.setSLA_Breached(false);
            ticket.setState(TicketState.RESOLVED);
            ticketRepository.save(ticket);
            System.out.println("RAG Response for " + ticket.getNumber());
            System.out.println("Answer: " + response.getBody().get("answer"));
            System.out.println("Sources: " + response.getBody().get("sources"));
        } catch (Exception e) {
            System.out.println("FastAPI call failed: " + e.getMessage());
        }
    }
}