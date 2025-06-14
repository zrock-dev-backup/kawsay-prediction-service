package api

import (
	"encoding/json"
	"net/http"
	"predictor/data"
	"predictor/utils"
	"testing"
)

func TestPrediction(t *testing.T) {
	t.Run("happy path", func(t *testing.T) {
		requestPayload := data.PredictionRequest{
			Records: []data.GradeRecord{
				{StudentID: 1001, CourseID: 41, Semester: 1, GradeLab: 95.5, GradeMasterclass: 92.0},
				{StudentID: 1002, CourseID: 21, Semester: 2, GradeLab: 65.0, GradeMasterclass: 88.0},
				{StudentID: 1001, CourseID: 11, Semester: 2, GradeLab: 90.0, GradeMasterclass: 61.5},
				{StudentID: 1003, CourseID: 31, Semester: 3, GradeLab: 85.0, GradeMasterclass: 89.0},
			},
		}
		resp, body := utils.MakeRequest(t, "POST", "/bulk-predict", requestPayload)
		utils.AssertStatusCode(t, resp, http.StatusOK, body)

		var predictions data.PredictionResponse
		if err := json.Unmarshal(body, &predictions); err != nil {
			t.Fatalf("Failed to unmarshal response: %v. Body: %s", err, string(body))
		}

		if len(predictions.Predictions) != 4 {
			t.Fatalf("Expected 4 predictions, got %d", len(predictions.Predictions))
		}

		// Create a map of predictions by studentID and courseID
		predictionMap := make(map[int]map[int]string)
		for _, pred := range predictions.Predictions {
			if _, exists := predictionMap[pred.StudentID]; !exists {
				predictionMap[pred.StudentID] = make(map[int]string)
			}
			predictionMap[pred.StudentID][pred.CourseID] = pred.PredictedOutcome
		}

		// Define expected outcomes
		expectedOutcomes := map[int]map[int]string{
			1001: {
				41: "PASS", // High grades
				11: "PASS", // Low masterclass grade
			},
			1002: {
				21: "PASS", // Low lab grade
			},
			1003: {
				31: "PASS", // Solid grades
			},
		}

		// Assert predictions
		for studentID, courses := range expectedOutcomes {
			studentPredictions, exists := predictionMap[studentID]
			if !exists {
				t.Errorf("No predictions found for student %d", studentID)
				continue
			}

			for courseID, expectedOutcome := range courses {
				actualOutcome, exists := studentPredictions[courseID]
				if !exists {
					t.Errorf("No prediction found for student %d, course %d", studentID, courseID)
					continue
				}
				if actualOutcome != expectedOutcome {
					t.Errorf("For student %d, course %d: expected %s, got %s",
						studentID, courseID, expectedOutcome, actualOutcome)
				}
			}
		}
	})
}
