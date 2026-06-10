package com.InternProject.demo.Config;

import org.apache.kafka.clients.admin.NewTopic;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.config.TopicBuilder;

@Configuration
public class KafkaTopicConfig {
    @Bean
    public NewTopic ticketsRawTopic() {
        return TopicBuilder.name("tickets.raw")
                .partitions(3)
                .replicas(1)
                .build();
    }
}