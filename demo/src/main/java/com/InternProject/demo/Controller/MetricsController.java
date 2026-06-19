package com.InternProject.demo.Controller;

import com.InternProject.demo.model.TicketMetrics;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
@RestController
public class MetricsController {

    @Autowired
    TicketMetrics ticketMetrics;

    @GetMapping(value = "/custom-metrics", produces = "text/plain")
    public String metrics() {
        return "# HELP tickets_ingested_total Total tickets received from Kafka\n" +
                "# TYPE tickets_ingested_total counter\n" +
                "tickets_ingested_total " + ticketMetrics.getTotalIngested() + "\n" +
                "# HELP tickets_resolved_total Total tickets resolved\n" +
                "# TYPE tickets_resolved_total counter\n" +
                "tickets_resolved_total " + ticketMetrics.getTotalResolved() + "\n" +
                "# HELP tickets_sla_breached_total SLA breaches\n" +
                "# TYPE tickets_sla_breached_total counter\n" +
                "tickets_sla_breached_total " + ticketMetrics.getTotalSLABreached() + "\n" +
                "# HELP tickets_fastapi_failures_total FastAPI failures\n" +
                "# TYPE tickets_fastapi_failures_total counter\n" +
                "tickets_fastapi_failures_total " + ticketMetrics.getTotalFastApiFailures() + "\n" +
                "# EOF\n";
    }
}