package com.InternProject.demo.Service;

import com.InternProject.demo.model.Ticket;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;

import static org.apache.kafka.common.requests.DeleteAclsResponse.log;

public class MailSenderService {
    @Autowired
    private JavaMailSender mailSender;
    private void sendReplyEmail(Ticket ticket, String answer,boolean slaBreached) {
        SimpleMailMessage mail = new SimpleMailMessage();

        mail.setTo(ticket.getAssignedTo());         // reply to original sender
        mail.setSubject("RE: " + ticket.getShortDescription() + " [" + ticket.getNumber() + "]");
        mail.setText(buildEmailBody(ticket, answer,slaBreached));

        mailSender.send(mail);
        log.info("Reply email sent for ticket: {}", ticket.getNumber());
    }

    private String buildEmailBody(Ticket ticket, String answer, boolean slaBreached) {
        return """
        Dear User,

        Your ticket %s has been resolved.

        Resolution:
        %s        

        Regards,
        Support Team
        """.formatted(
                ticket.getNumber(),
                answer,
                slaBreached ? "⚠️ Note: This ticket exceeded its SLA deadline." : ""
        );
    }
}
