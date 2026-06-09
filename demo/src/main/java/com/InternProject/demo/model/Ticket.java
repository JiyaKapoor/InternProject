package com.InternProject.demo.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class Ticket {
    private String number;
    private boolean active;
    private int priority;
    private String shortDescription;
    private String assignmentGroup;
    private String state;
    private String assignedTo;
    private LocalDateTime sysCreatedOn;
    private LocalDateTime resolvedAt;
}
