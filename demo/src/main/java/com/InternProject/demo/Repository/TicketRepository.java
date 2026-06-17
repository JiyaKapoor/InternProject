package com.InternProject.demo.Repository;

import com.InternProject.demo.model.Ticket;
import org.springframework.data.jpa.repository.JpaRepository;

public interface TicketRepository extends JpaRepository<Ticket,String>{
}
