package data

type GradeRecord struct {
	StudentID        int     `json:"studentId"`
	CourseID         int     `json:"courseId"`
	Semester         int     `json:"semester"`
	GradeLab         float64 `json:"grade_lab"`
	GradeMasterclass float64 `json:"grade_masterclass"`
}

type PredictionRequest struct {
	Records []GradeRecord `json:"records"`
}

type Prediction struct {
	StudentID        int      `json:"studentId"`
	CourseID         int      `json:"courseId"`
	Semester         int      `json:"semester"`
	PredictedOutcome string   `json:"predictedOutcome"`
	Confidence       float64  `json:"confidence"`
	Drivers          []string `json:"drivers"`
}

type PredictionResponse struct {
	Predictions []Prediction `json:"predictions"`
}
