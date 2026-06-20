package com.InternProject.demo.model;


import jakarta.persistence.*;


import java.time.LocalDateTime;

@Entity
public class Ticket {
    @Id
    private String number;
    private boolean active;
    private int priority;
    private String shortDescription;
    @Column(columnDefinition = "TEXT")
    private String resolution;
    private String userEmail;
    private String assignmentGroup;
    @Enumerated(EnumType.STRING)
    @Column(name = "state")
    private TicketState state;
    private String assignedTo;
    private LocalDateTime sysCreatedOn;
    private LocalDateTime resolvedAt;
    private boolean SLA_Breached;
    private LocalDateTime SLADue;
    public void setUserEmail(String email){
        this.userEmail=email;
    }
    public String getUserEmail(){
        return this.userEmail;
    }
    public void setSLADue(LocalDateTime time){
        this.SLADue=time;
    }
    public LocalDateTime getSLADue(){
        return this.SLADue;
    }
    public void setResolution(String resolution){
        this.resolution=resolution;
    }
    public String getResolution(){
        return this.resolution;
    }
    public void setSLA_Breached(boolean flag){
        this.SLA_Breached=flag;
    }
    public boolean getSLA_Breached(){
        return this.SLA_Breached;
    }
    public String getNumber() {
        return number;
    }

    public void setNumber(String number) {
        this.number = number;
    }

    public boolean isActive() {
        return active;
    }

    public void setActive(boolean active) {
        this.active = active;
    }

    public int getPriority() {
        return priority;
    }

    public void setPriority(int priority) {
        this.priority = priority;
    }

    public String getShortDescription() {
        return shortDescription;
    }
    public void setShortDescription(String shortDescription) {
        this.shortDescription = shortDescription;
    }

    public String getAssignmentGroup() {
        return assignmentGroup;
    }

    public void setAssignmentGroup(String assignmentGroup) {
        this.assignmentGroup = assignmentGroup;
    }

    public TicketState getState() {
        return state;
    }

    public void setState(TicketState state) {
        this.state = state;
    }

    public String getAssignedTo() {
        return assignedTo;
    }

    public void setAssignedTo(String assignedTo) {
        this.assignedTo = assignedTo;
    }

    public LocalDateTime getSysCreatedOn() {
        return sysCreatedOn;
    }

    public void setSysCreatedOn(LocalDateTime sysCreatedOn) {
        this.sysCreatedOn = sysCreatedOn;
    }

    public LocalDateTime getResolvedAt() {
        return resolvedAt;
    }

    public void setResolvedAt(LocalDateTime resolvedAt) {
        this.resolvedAt = resolvedAt;
    }
}
