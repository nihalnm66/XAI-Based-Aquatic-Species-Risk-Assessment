package com.aquaculture.backend_orchestrator;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        // user.dir points to your Backend_Service folder
        String projectDir = System.getProperty("user.dir");

        // 1. Serve the output images so they can be viewed
        String outputDirPath = "file:" + projectDir + "/src/main/resources/static/outputs/";
        registry.addResourceHandler("/outputs/**")
                .addResourceLocations(outputDirPath);

        // 2. Serve your completely separate Frontend folder!
        // The "/../" tells it to go up one level and look inside the Frontend folder
        String frontendDirPath = "file:" + projectDir + "/../Frontend/";
        registry.addResourceHandler("/**")
                .addResourceLocations(frontendDirPath);
    }
}