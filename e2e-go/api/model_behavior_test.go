package api

import (
	"encoding/json"
	"net/http"
	"predictor/data"
	"predictor/utils"
	"testing"

	"github.com/stretchr/testify/assert"
)

// TestModelBehavior uses a table-driven approach for ML-specific validation.
func TestModelBehavior(t *testing.T) {
	testCases := []struct {
		name           string
		payload        data.PredictionRequest
		expectedStatus int
		assertion      func(t *testing.T, body []byte)
	}{
		{
			name:           "Model Invariance to Identifier (studentId)",
			expectedStatus: http.StatusOK,
			payload: data.PredictionRequest{
				Records: []data.GradeRecord{
					// These two records are identical except for studentId
					{StudentID: 1001, CourseID: 41, Semester: 1, GradeLab: 95.0, GradeMasterclass: 92.0},
					{StudentID: 9999, CourseID: 41, Semester: 1, GradeLab: 95.0, GradeMasterclass: 92.0},
				},
			},
			assertion: func(t *testing.T, body []byte) {
				var resp data.PredictionResponse
				err := json.Unmarshal(body, &resp)
				assert.NoError(t, err)
				assert.Len(t, resp.Predictions, 2)

				// The predictions should be identical in outcome and confidence
				assert.Equal(t, resp.Predictions[0].PredictedOutcome, resp.Predictions[1].PredictedOutcome)
				assert.InDelta(t, resp.Predictions[0].Confidence, resp.Predictions[1].Confidence, 0.0001)
			},
		},
		{
			name:           "Handles Out-of-Distribution Categorical Value",
			expectedStatus: http.StatusUnprocessableEntity, // The API should reject values not in the model's vocabulary
			payload: data.PredictionRequest{
				Records: []data.GradeRecord{
					// courseId 999 is not in the model's known categories [2, 11, 21, 31, 41]
					{StudentID: 3001, CourseID: 999, Semester: 1, GradeLab: 80.0, GradeMasterclass: 80.0},
				},
			},
			assertion: nil, // We only care about the validation failure status
		},
		{
			name:           "Model Monotonicity (Higher Grades -> Higher PASS Confidence)",
			expectedStatus: http.StatusOK,
			payload: data.PredictionRequest{
				Records: []data.GradeRecord{
					// Baseline record
					{StudentID: 4001, CourseID: 21, Semester: 2, GradeLab: 80.0, GradeMasterclass: 80.0},
					// Improved record - same everything, but higher grades
					{StudentID: 4002, CourseID: 21, Semester: 2, GradeLab: 95.0, GradeMasterclass: 95.0},
				},
			},
			assertion: func(t *testing.T, body []byte) {
				var resp data.PredictionResponse
				err := json.Unmarshal(body, &resp)
				assert.NoError(t, err)
				assert.Len(t, resp.Predictions, 2)

				// Both should PASS, but the second should have higher confidence
				pBaseline := resp.Predictions[0]
				pImproved := resp.Predictions[1]

				assert.Equal(t, "PASS", pBaseline.PredictedOutcome, "Baseline should pass")
				assert.Equal(t, "PASS", pImproved.PredictedOutcome, "Improved should pass")
				assert.Greater(t, pImproved.Confidence, pBaseline.Confidence, "Higher grades should result in higher confidence")
			},
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			resp, body := utils.MakeRequest(t, "POST", "/bulk-predict", tc.payload)
			utils.AssertStatusCode(t, resp, tc.expectedStatus, body)
			if tc.assertion != nil {
				tc.assertion(t, body)
			}
		})
	}
}
