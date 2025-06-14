package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"predictor/data"
	"time"
)

const (
	predictorURL = "http://localhost:8000/bulk-predict"
)

func main() {
	log.Println("--- Kawsay Prediction Service Integration Test ---")

	requestPayload := data.PredictionRequest{
		Records: []data.GradeRecord{
			// Scenario 1: Expected to PASS (high grades)
			{StudentID: 1001, CourseID: 41, Semester: 1, GradeLab: 95.5, GradeMasterclass: 92.0},
			// Scenario 2: Expected to FAIL (low lab grade)
			{StudentID: 1002, CourseID: 21, Semester: 2, GradeLab: 65.0, GradeMasterclass: 88.0},
			// Scenario 3: Expected to FAIL (low masterclass grade)
			{StudentID: 1001, CourseID: 11, Semester: 2, GradeLab: 90.0, GradeMasterclass: 61.5},
			// Scenario 4: Expected to PASS (another student, solid grades)
			{StudentID: 1003, CourseID: 31, Semester: 3, GradeLab: 85.0, GradeMasterclass: 89.0},
		},
	}
	log.Printf("-> Preparing to send %d records to %s\n", len(requestPayload.Records), predictorURL)

	// 2. Marshal the Go struct into a JSON byte slice.
	jsonData, err := json.Marshal(requestPayload)
	if err != nil {
		log.Fatalf("Error marshaling JSON: %v", err)
	}

	// 3. Create an HTTP client with a timeout for robustness.
	client := &http.Client{Timeout: 10 * time.Second}

	// 4. Create the HTTP POST request.
	req, err := http.NewRequest("POST", predictorURL, bytes.NewBuffer(jsonData))
	if err != nil {
		log.Fatalf("Error creating HTTP request: %v", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")

	// 5. Execute the request.
	resp, err := client.Do(req)
	if err != nil {
		log.Fatalf("Error sending request to prediction service: %v\nIs the service running on localhost:8000?", err)
	}
	defer resp.Body.Close()

	// 6. Read the response body.
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Fatalf("Error reading response body: %v", err)
	}

	// 7. Check the HTTP status code.
	if resp.StatusCode != http.StatusOK {
		log.Fatalf("API returned a non-200 status code: %d\nResponse body: %s", resp.StatusCode, string(body))
	}
	log.Println("<- Received successful 200 OK response from API.")

	// 8. Unmarshal the JSON response into our Go struct.
	var predictionResponse data.PredictionResponse
	if err := json.Unmarshal(body, &predictionResponse); err != nil {
		log.Fatalf("Error unmarshaling response JSON: %v", err)
	}

	// 9. Display the results in a formatted way.
	fmt.Println("\n--- Prediction Results ---")
	fmt.Println("-------------------------------------------------------------------------------------------------")
	fmt.Printf("%-12s | %-10s | %-10s | %-10s | %-12s | %s\n", "Student ID", "Course ID", "Semester", "Outcome", "Confidence", "Drivers")
	fmt.Println("-------------------------------------------------------------------------------------------------")
	for _, p := range predictionResponse.Predictions {
		fmt.Printf("%-12d | %-10d | %-10d | %-10s | %-12.2f | %v\n",
			p.StudentID,
			p.CourseID,
			p.Semester,
			p.PredictedOutcome,
			p.Confidence,
			p.Drivers,
		)
	}
}
