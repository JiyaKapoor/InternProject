package com.InternProject.demo.Service;

import com.InternProject.demo.model.Ticket;
import com.InternProject.demo.model.TicketState;
import org.springframework.stereotype.Service;
import java.time.LocalDateTime;
import java.util.Map;

@Service
public class EmailToTicketParser {

    public Ticket parse(Map<String, Object> emailData) {
        String subject = (String) emailData.get("subject");
        String body = (String) emailData.get("body");
        String from = (String) emailData.get("from");


        Ticket ticket = new Ticket();
        ticket.setNumber("TKT-" + System.currentTimeMillis());
        ticket.setActive(true);
        ticket.setState(TicketState.NEW);
        ticket.setSLADue(LocalDateTime.now().plusHours(8));
        ticket.setSysCreatedOn(LocalDateTime.now());
        ticket.setAssignedTo(from);
        ticket.setPriority(3);
        ticket.setAssignmentGroup("General IT");

        // Extract short description from body
        String shortDesc = extractShortDescription(body);
        ticket.setShortDescription(shortDesc);

        return ticket;
    }

    private String extractShortDescription(String body) {
        if (body == null || body.isBlank()) return "No description provided";

        String cleaned = body
                .replaceAll("(?i)^(dear|hi|hello|hey)\\s+.*?(\\n|,)", "")
                .replaceAll("(?i)(regards|thanks|thank you|sincerely).*$", "")
                .trim();

        String[] sentences = cleaned.split("(?<=[.!?])\\s+");
        for (String sentence : sentences) {
            String s = sentence.trim();
            if (s.length() > 10) {
                // Truncate to 100 chars for shortDescription
                return s.length() > 100 ? s.substring(0, 100) + "..." : s;
            }
        }

        return cleaned.length() > 100 ? cleaned.substring(0, 100) + "..." : cleaned;
    }
}