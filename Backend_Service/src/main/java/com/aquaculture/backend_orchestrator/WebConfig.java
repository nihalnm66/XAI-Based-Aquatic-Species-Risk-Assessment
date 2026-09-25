package com.aquaculture.backend_orchestrator; // Update this package if your WebConfig is inside a 'config' folder

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.nio.file.Path;
import java.nio.file.Paths;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        // Find the absolute physical path to your outputs folder
        String projectDir = System.getProperty("user.dir");
        String outputDir = Paths.get(projectDir, "src", "main", "resources", "static", "outputs").toFile().getAbsolutePath();

        // Tell Spring to serve requests to /outputs/** directly from that physical folder
        registry.addResourceHandler("/outputs/**")
                .addResourceLocations("file:" + outputDir + "/");
    }
}