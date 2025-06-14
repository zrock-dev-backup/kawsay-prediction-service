package api

import (
	"encoding/json"
	"net/http"
	"predictor/data"
	"predictor/utils"
	"testing"

	"github.com/stretchr/testify/assert"
)

// TestBulkPredictEndpoint uses a table-driven approach to test various scenarios.
func TestBulkPredictEndpoint(t *testing.T) {
	// testCases defines all scenarios for the /bulk-predict endpoint.
	testCases := []struct {
		name           string
		payload        data.PredictionRequest
		expectedStatus int
		assertion      func(t *testing.T, body []byte, payload data.PredictionRequest)
	}{
		{
			name:           "Happy Path - Valid Mix of Records",
			expectedStatus: http.StatusOK,
			payload: data.PredictionRequest{
				Records: []data.GradeRecord{
					{StudentID: 1001, CourseID: 41, Semester: 1, GradeLab: 95.5, GradeMasterclass: 92.0},
					{StudentID: 1002, CourseID: 21, Semester: 2, GradeLab: 65.0, GradeMasterclass: 88.0},
					{StudentID: 1001, CourseID: 11, Semester: 2, GradeLab: 90.0, GradeMasterclass: 61.5},
					{StudentID: 1003, CourseID: 31, Semester: 3, GradeLab: 85.0, GradeMasterclass: 89.0},
				},
			},
			assertion: func(t *testing.T, body []byte, payload data.PredictionRequest) {
				var resp data.PredictionResponse
				err := json.Unmarshal(body, &resp)
				assert.NoError(t, err, "Failed to unmarshal response body")
				assert.Len(t, resp.Predictions, 4, "Expected 4 predictions")

				// Simple check for one of the outcomes
				for _, p := range resp.Predictions {
					if p.StudentID == 1001 && p.CourseID == 41 {
						assert.Equal(t, "PASS", p.PredictedOutcome, "Expected student 1001 in course 41 to PASS")
					}
				}
			},
		},
		{
			name:           "Validation Error - Empty Records Array",
			expectedStatus: http.StatusUnprocessableEntity, // 422 is standard for validation errors
			payload: data.PredictionRequest{
				Records: []data.GradeRecord{},
			},
			assertion: nil,
		},
		{
			name:           "Validation Error - Grade Out of Bounds",
			expectedStatus: http.StatusUnprocessableEntity,
			payload: data.PredictionRequest{
				Records: []data.GradeRecord{
					// grade_lab > 100, which violates the predictor service api spec
					{StudentID: 2001, CourseID: 41, Semester: 1, GradeLab: 101.0, GradeMasterclass: 92.0},
				},
			},
			assertion: nil,
		},
		{
			name:           "Validation Error - Missing Required Field",
			expectedStatus: http.StatusUnprocessableEntity,
			// raw json
			payload:   data.PredictionRequest{}, // This will be ignored in favor of a custom body
			assertion: nil,
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			var resp *http.Response
			var body []byte

			// Special case for malformed JSON payload
			if tc.name == "Validation Error - Missing Required Field" {
				// The 'grade_lab' field is intentionally omitted.
				jsonPayload := `{"records": [{"studentId": 2002, "courseId": 21, "semester": 2, "grade_masterclass": 88.0}]}`
				resp, body = utils.MakeRequest(t, "POST", "/bulk-predict", []byte(jsonPayload))
			} else {
				resp, body = utils.MakeRequest(t, "POST", "/bulk-predict", tc.payload)
			}
			utils.AssertStatusCode(t, resp, tc.expectedStatus, body)
			if tc.assertion != nil {
				tc.assertion(t, body, tc.payload)
			}
		})
	}
}
