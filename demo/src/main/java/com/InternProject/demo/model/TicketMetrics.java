package com.InternProject.demo.model;

import org.springframework.stereotype.Component;

@Component
public class TicketMetrics {

    private int totalIngested = 0;
    private int totalResolved = 0;
    private int totalSLABreached = 0;
    private int totalFastApiFailures = 0;

    public void recordIngestion() { totalIngested++; }
    public void recordResolved() { totalResolved++; }
    public void recordSLABreach() { totalSLABreached++; }
    public void recordFastApiFailure() { totalFastApiFailures++; }

    public int getTotalIngested() { return totalIngested; }
    public int getTotalResolved() { return totalResolved; }
    public int getTotalSLABreached() { return totalSLABreached; }
    public int getTotalFastApiFailures() { return totalFastApiFailures; }
}