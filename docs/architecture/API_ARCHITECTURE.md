# Dars AI Tutoring Platform - API Architecture & Contracts

**Date:** 2026-01-28
**Version:** 1.0
**Status:** Ready for Implementation

---

## Table of Contents

1. Architecture Overview
2. REST API Specification (OpenAPI 3.0)
3. Internal Service Contracts (TypeScript)
4. Error Handling Standards
5. Authentication & Security
6. Request/Response Examples
7. Implementation Checklist

---

# PART 1: ARCHITECTURE OVERVIEW

## System Components

```
┌─────────────────────────────────────────────────────┐
│                  CLIENTS                            │
├──────────────────┬──────────────────┬───────────────┤
│  Telegram Bot    │  Admin Web UI    │  Future Apps  │
│  (Webhook)       │  (HTML/JS)       │  (Mobile)     │
└──────┬───────────┴──────┬───────────┴───────┬───────┘
       │                  │                   │
       └──────────────────┼───────────────────┘
                          │
                    ┌─────▼──────────┐
                    │  FastAPI       │
                    │  Backend       │
                    └─────┬──────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
    ┌───▼────┐      ┌────▼─────┐    ┌─────▼──────┐
    │Database│      │Claude API│    │Telegram    │
    │        │      │(Hints)   │    │Bot API     │
    └────────┘      └──────────┘    └────────────┘
```

## API Layers

### Layer 1: REST API (HTTP)
- FastAPI serves HTTP endpoints
- JSON request/response format
- Authentication via token in headers

### Layer 2: Telegram Bot
- WebHook receives Telegram updates
- Message handlers process commands
- Callbacks send responses back

### Layer 3: Internal Services
- Problem selection algorithm
- Answer evaluation
- Streak calculation
- Hint generation
- Cost tracking

---

# PART 2: REST API SPECIFICATION

## OpenAPI 3.0 Specification

```yaml
openapi: 3.0.0
info:
  title: Dars AI Tutoring Platform API
  version: 1.0.0
  description: REST API for Dars tutoring backend

servers:
  - url: https://dars.railway.app
    description: Production
  - url: http://localhost:8000
    description: Local development

# ============================================================================
# TELEGRAM WEBHOOK
# ============================================================================

paths:
  /webhook:
    post:
      summary: Telegram Bot Webhook
      description: Receives updates from Telegram Bot API
      tags:
        - Telegram
      security:
        - BearerToken: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TelegramUpdate'
            example:
              update_id: 123456789
              message:
                message_id: 1
                date: 1643129200
                chat:
                  id: 987654321
                  type: private
                from:
                  id: 987654321
                  is_bot: false
                  first_name: Rajesh
                text: /start

      responses:
        '200':
          description: Update processed successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: ok
                  message_id:
                    type: integer
                    example: 1

        '400':
          $ref: '#/components/responses/BadRequest'

        '401':
          $ref: '#/components/responses/Unauthorized'

        '500':
          $ref: '#/components/responses/InternalError'

# ============================================================================
# HEALTH CHECK
# ============================================================================

  /health:
    get:
      summary: Health Check
      description: Check if system is operational
      tags:
        - System
      responses:
        '200':
          description: System healthy
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HealthCheck'
              example:
                status: ok
                db: ok
                claude: ok
                timestamp: '2026-01-28T10:30:00Z'

        '503':
          description: Service unavailable
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HealthCheck'
              example:
                status: error
                db: timeout
                claude: ok
                timestamp: '2026-01-28T10:30:00Z'

# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

  /admin/stats:
    get:
      summary: Get system statistics
      description: Returns overall platform metrics
      tags:
        - Admin
      security:
        - AdminAuth: []
      responses:
        '200':
          description: Statistics retrieved
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AdminStats'
              example:
                total_students: 50
                active_this_week: 42
                avg_streak: 7.2
                avg_problems_per_session: 4.8
                total_sessions: 342
                timestamp: '2026-01-28T10:30:00Z'

        '401':
          $ref: '#/components/responses/Unauthorized'

        '403':
          $ref: '#/components/responses/Forbidden'

  /admin/students:
    get:
      summary: List all students
      description: Returns paginated list of students
      tags:
        - Admin
      security:
        - AdminAuth: []
      parameters:
        - name: grade
          in: query
          schema:
            type: integer
            enum: [6, 7, 8]
          description: Filter by grade (optional)

        - name: page
          in: query
          schema:
            type: integer
            default: 1
          description: Page number for pagination

        - name: limit
          in: query
          schema:
            type: integer
            default: 20
            maximum: 100

      responses:
        '200':
          description: Student list
          content:
            application/json:
              schema:
                type: object
                properties:
                  students:
                    type: array
                    items:
                      $ref: '#/components/schemas/StudentProfile'
                  total:
                    type: integer
                  page:
                    type: integer
                  limit:
                    type: integer

              example:
                students:
                  - student_id: 1
                    telegram_id: 987654321
                    name: Rajesh
                    grade: 7
                    language: bn
                    current_streak: 12
                    longest_streak: 28
                    avg_accuracy: 72.5
                    last_practice: '2026-01-28T09:30:00Z'
                    created_at: '2026-01-15T10:00:00Z'
                total: 50
                page: 1
                limit: 20

        '401':
          $ref: '#/components/responses/Unauthorized'

  /admin/cost:
    get:
      summary: Get cost summary
      description: Returns cost metrics (AI + infrastructure)
      tags:
        - Admin
      security:
        - AdminAuth: []
      parameters:
        - name: period
          in: query
          schema:
            type: string
            enum: [day, week, month]
            default: week

      responses:
        '200':
          description: Cost data
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CostSummary'
              example:
                period: week
                total_cost: 1.23
                daily_average: 0.18
                projected_monthly: 7.80
                per_student_cost: 0.16
                claude_cost: 1.10
                infrastructure_cost: 0.13
                alert: true
                alert_message: Over budget - exceeds $0.15/student/month
                timestamp: '2026-01-28T10:30:00Z'

        '401':
          $ref: '#/components/responses/Unauthorized'

# ============================================================================
# STUDENT ENDPOINTS (Telegram → REST interface)
# ============================================================================
# These endpoints mirror the Telegram bot functionality and are used by:
# - Stream D (Learning): Practice flow, hints, evaluation
# - Stream B (Frontend): Web UI for students (future)

  /practice:
    get:
      summary: Get daily practice problems
      description: Returns 5 problems for student's daily practice session
      tags:
        - Student Practice
      security:
        - StudentAuth: []
      responses:
        '200':
          description: Practice problems retrieved
          content:
            application/json:
              schema:
                type: object
                properties:
                  session_id:
                    type: integer
                  problems:
                    type: array
                    items:
                      $ref: '#/components/schemas/ProblemWithoutAnswer'
                  problem_count:
                    type: integer
                    example: 5
                  expires_at:
                    type: string
                    format: date-time
              example:
                session_id: 42
                problems: []
                problem_count: 5
                expires_at: '2026-01-28T11:15:00Z'

        '401':
          $ref: '#/components/responses/Unauthorized'

        '404':
          description: Student not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiError'

  /practice/{problem_id}/answer:
    post:
      summary: Submit answer to a problem
      description: Evaluate student's answer and provide feedback
      tags:
        - Student Practice
      security:
        - StudentAuth: []
      parameters:
        - name: problem_id
          in: path
          required: true
          schema:
            type: integer

      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                session_id:
                  type: integer
                student_answer:
                  type: string
                  example: "75"
                time_spent_seconds:
                  type: integer
                  example: 45

      responses:
        '200':
          description: Answer evaluated
          content:
            application/json:
              schema:
                type: object
                properties:
                  is_correct:
                    type: boolean
                  feedback_text:
                    type: string
                  next_problem_id:
                    type: integer
                    nullable: true
                    description: Null if session complete

        '400':
          $ref: '#/components/responses/BadRequest'

        '401':
          $ref: '#/components/responses/Unauthorized'

  /practice/{problem_id}/hint:
    post:
      summary: Request a hint
      description: Generate Socratic hint for current problem (max 3 per problem)
      tags:
        - Student Practice
      security:
        - StudentAuth: []
      parameters:
        - name: problem_id
          in: path
          required: true
          schema:
            type: integer

      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                session_id:
                  type: integer
                student_answer:
                  type: string
                hint_number:
                  type: integer
                  enum: [1, 2, 3]

      responses:
        '200':
          description: Hint generated
          content:
            application/json:
              schema:
                type: object
                properties:
                  hint_text:
                    type: string
                  hint_number:
                    type: integer
                  hints_remaining:
                    type: integer

        '400':
          description: Invalid request (e.g., too many hints)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiError'

        '401':
          $ref: '#/components/responses/Unauthorized'

  /streak:
    get:
      summary: Get student's streak information
      description: Returns current streak, longest streak, and milestone achievements
      tags:
        - Student Engagement
      security:
        - StudentAuth: []
      responses:
        '200':
          description: Streak data retrieved
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Streak'

        '401':
          $ref: '#/components/responses/Unauthorized'

  /student/profile:
    get:
      summary: Get student profile
      description: Returns student's learning progress and preferences
      tags:
        - Student
      security:
        - StudentAuth: []
      responses:
        '200':
          description: Profile retrieved
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/StudentProfile'

        '401':
          $ref: '#/components/responses/Unauthorized'

    patch:
      summary: Update student preferences
      description: Update language, grade, or other settings
      tags:
        - Student
      security:
        - StudentAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                language:
                  type: string
                  enum: ['en', 'bn']
                grade:
                  type: integer
                  enum: [6, 7, 8]

      responses:
        '200':
          description: Profile updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/StudentProfile'

        '400':
          $ref: '#/components/responses/BadRequest'

        '401':
          $ref: '#/components/responses/Unauthorized'

# ============================================================================
# COMPONENTS (Schemas)
# ============================================================================

components:

  securitySchemes:
    BearerToken:
      type: http
      scheme: bearer
      description: Telegram bot token in Authorization header

    AdminAuth:
      type: apiKey
      in: header
      name: X-Admin-ID
      description: Admin telegram ID (Phase 0), JWT token (Phase 1)

    StudentAuth:
      type: apiKey
      in: header
      name: X-Student-ID
      description: Student telegram ID (Phase 0), JWT/session token (Phase 1+)

  schemas:

    # ========================================================================
    # TELEGRAM WEBHOOK
    # ========================================================================

    TelegramUpdate:
      type: object
      required:
        - update_id
      properties:
        update_id:
          type: integer
          description: Telegram update ID (unique, sequential)

        message:
          $ref: '#/components/schemas/TelegramMessage'

    TelegramMessage:
      type: object
      required:
        - message_id
        - date
        - chat
        - from
      properties:
        message_id:
          type: integer

        date:
          type: integer
          description: Unix timestamp

        chat:
          type: object
          required:
            - id
            - type
          properties:
            id:
              type: integer
              description: Chat ID (negative for groups, positive for private)
            type:
              type: string
              enum: [private, group, supergroup, channel]

        from:
          type: object
          required:
            - id
            - is_bot
            - first_name
          properties:
            id:
              type: integer
              description: User ID
            is_bot:
              type: boolean
            first_name:
              type: string
            last_name:
              type: string
            username:
              type: string

        text:
          type: string
          description: Message text (optional, only if text message)

        callback_query:
          type: object
          description: Callback from inline button press
          properties:
            id:
              type: string
            from:
              $ref: '#/components/schemas/TelegramUser'
            data:
              type: string
              description: Callback data from button

    TelegramUser:
      type: object
      required:
        - id
        - is_bot
        - first_name
      properties:
        id:
          type: integer
        is_bot:
          type: boolean
        first_name:
          type: string
        last_name:
          type: string

    # ========================================================================
    # HEALTH CHECK
    # ========================================================================

    HealthCheck:
      type: object
      required:
        - status
        - timestamp
      properties:
        status:
          type: string
          enum: [ok, error]

        db:
          type: string
          enum: [ok, timeout, error]
          description: Database connection status

        claude:
          type: string
          enum: [ok, timeout, error]
          description: Claude API status

        timestamp:
          type: string
          format: date-time

    # ========================================================================
    # ADMIN STATISTICS
    # ========================================================================

    AdminStats:
      type: object
      required:
        - total_students
        - active_this_week
        - avg_streak
        - avg_problems_per_session
        - total_sessions
        - timestamp
      properties:
        total_students:
          type: integer
          example: 50

        active_this_week:
          type: integer
          example: 42

        active_this_week_percent:
          type: number
          format: float
          example: 84.0

        avg_streak:
          type: number
          format: float
          example: 7.2

        avg_problems_per_session:
          type: number
          format: float
          example: 4.8

        total_sessions:
          type: integer
          example: 342

        timestamp:
          type: string
          format: date-time

    # ========================================================================
    # STUDENT PROFILE
    # ========================================================================

    StudentProfile:
      type: object
      required:
        - student_id
        - telegram_id
        - name
        - grade
        - language
        - current_streak
        - longest_streak
        - avg_accuracy
        - last_practice
        - created_at
      properties:
        student_id:
          type: integer

        telegram_id:
          type: integer
          description: Telegram user ID

        name:
          type: string
          maxLength: 100

        grade:
          type: integer
          enum: [6, 7, 8]

        language:
          type: string
          enum: [bn, en]

        current_streak:
          type: integer
          minimum: 0

        longest_streak:
          type: integer
          minimum: 0

        avg_accuracy:
          type: number
          format: float
          minimum: 0
          maximum: 100
          description: Percentage correct answers

        last_practice:
          type: string
          format: date-time
          nullable: true

        created_at:
          type: string
          format: date-time

        updated_at:
          type: string
          format: date-time

    # ========================================================================
    # PROBLEMS (Full & Without Answers)
    # ========================================================================

    Problem:
      type: object
      required:
        - problem_id
        - grade
        - topic
        - question_en
        - question_bn
        - answer
        - difficulty
        - hints
      properties:
        problem_id:
          type: integer

        grade:
          type: integer
          enum: [6, 7, 8]

        topic:
          type: string
          description: Topic/subject area

        question_en:
          type: string
          description: Problem statement in English

        question_bn:
          type: string
          description: Problem statement in Bengali

        answer:
          type: string
          description: Correct answer (for evaluation only - never shown to student before answer)

        answer_type:
          type: string
          enum: [numeric, multiple_choice, text]
          default: numeric

        difficulty:
          type: integer
          enum: [1, 2, 3]
          description: "1=Easy, 2=Medium, 3=Hard"

        hints:
          type: array
          maxItems: 3
          items:
            type: object
            properties:
              hint_number:
                type: integer
                enum: [1, 2, 3]
              text_en:
                type: string
              text_bn:
                type: string

        acceptable_tolerance_percent:
          type: number
          default: 5
          description: For numeric answers, tolerance for acceptance

        multiple_choice_options:
          type: array
          description: Options for multiple choice problems
          items:
            type: object
            properties:
              index:
                type: integer
              text_en:
                type: string
              text_bn:
                type: string
              is_correct:
                type: boolean

        created_at:
          type: string
          format: date-time

    ProblemWithoutAnswer:
      type: object
      required:
        - problem_id
        - grade
        - topic
        - question_en
        - question_bn
        - difficulty
      properties:
        problem_id:
          type: integer

        grade:
          type: integer
          enum: [6, 7, 8]

        topic:
          type: string

        question_en:
          type: string

        question_bn:
          type: string

        difficulty:
          type: integer
          enum: [1, 2, 3]

        answer_type:
          type: string
          enum: [numeric, multiple_choice, text]

        multiple_choice_options:
          type: array
          items:
            type: object
            properties:
              index:
                type: integer
              text_en:
                type: string
              text_bn:
                type: string

    # ========================================================================
    # COST SUMMARY
    # ========================================================================

    CostSummary:
      type: object
      required:
        - period
        - total_cost
        - daily_average
        - projected_monthly
        - per_student_cost
        - timestamp
      properties:
        period:
          type: string
          enum: [day, week, month]

        total_cost:
          type: number
          format: float
          description: Total cost in USD

        daily_average:
          type: number
          format: float
          description: Average cost per day in USD

        projected_monthly:
          type: number
          format: float
          description: Cost projection for full month in USD

        per_student_cost:
          type: number
          format: float
          description: Average cost per student in USD

        claude_cost:
          type: number
          format: float
          description: AI API costs in USD

        infrastructure_cost:
          type: number
          format: float
          description: Server/DB costs in USD

        alert:
          type: boolean
          description: True if over budget

        alert_message:
          type: string
          nullable: true

        timestamp:
          type: string
          format: date-time

    # ========================================================================
    # ERROR RESPONSE
    # ========================================================================

    ErrorResponse:
      type: object
      required:
        - error
        - message
        - timestamp
      properties:
        error:
          type: string
          enum:
            - bad_request
            - unauthorized
            - forbidden
            - not_found
            - internal_error
            - service_unavailable

        message:
          type: string
          description: Human-readable error message

        error_code:
          type: string
          description: Machine-readable error code (e.g., ERR_AUTH_FAILED)

        details:
          type: object
          description: Additional error details
          nullable: true

        timestamp:
          type: string
          format: date-time

        request_id:
          type: string
          description: Correlation ID for debugging

  responses:
    BadRequest:
      description: Invalid request
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          example:
            error: bad_request
            message: Invalid request payload
            error_code: ERR_INVALID_JSON
            timestamp: '2026-01-28T10:30:00Z'
            request_id: req_123456789

    Unauthorized:
      description: Authentication failed
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          example:
            error: unauthorized
            message: Invalid or missing authentication token
            error_code: ERR_AUTH_FAILED
            timestamp: '2026-01-28T10:30:00Z'
            request_id: req_123456789

    Forbidden:
      description: Not authorized for this resource
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          example:
            error: forbidden
            message: Only admins can access this endpoint
            error_code: ERR_ADMIN_ONLY
            timestamp: '2026-01-28T10:30:00Z'
            request_id: req_123456789

    InternalError:
      description: Internal server error
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          example:
            error: internal_error
            message: Something went wrong processing your request
            error_code: ERR_INTERNAL
            timestamp: '2026-01-28T10:30:00Z'
            request_id: req_123456789
```

---

# PART 3: INTERNAL SERVICE CONTRACTS

## TypeScript Interface Definitions

### 3.1 Data Models

```typescript
// ============================================================================
// CORE DATA MODELS
// ============================================================================

/**
 * Student profile representing a learner in the system
 */
export interface Student {
  student_id: number;
  telegram_id: number;
  name: string;
  grade: 6 | 7 | 8;
  language: 'bn' | 'en'; // Bengali or English
  created_at: Date;
  updated_at: Date;
}

/**
 * Problem in the content library
 */
export interface Problem {
  problem_id: number;
  grade: 6 | 7 | 8;
  topic: string; // e.g., "Profit & Loss", "Fractions"
  subtopic?: string;

  // Content
  question_en: string;
  question_bn: string;
  answer: string; // Accept format: "75 rupees" or "75"
  hints: Hint[]; // Array of 3 hints

  // Metadata
  difficulty: 1 | 2 | 3; // 1=easy, 2=medium, 3=hard
  estimated_time_minutes: number;
  created_at: Date;
  updated_at: Date;
}

/**
 * Hint for guiding students without giving answer
 */
export interface Hint {
  hint_number: 1 | 2 | 3;
  text_en: string;
  text_bn: string;
  is_ai_generated: boolean;
}

/**
 * Practice session (one 5-problem session)
 */
export interface Session {
  session_id: number;
  student_id: number;
  date: Date;

  // Session state
  status: 'in_progress' | 'completed' | 'abandoned';
  problem_ids: number[]; // Which 5 problems selected
  responses: Response[]; // Answers to those problems

  // Timing
  created_at: Date;
  completed_at?: Date;
  expires_at: Date; // 30 minutes after start

  // Analytics
  total_time_seconds: number;
  problems_correct: number;
}

/**
 * Student's answer to a problem
 */
export interface Response {
  response_id: number;
  session_id: number;
  problem_id: number;

  // Answer data
  student_answer: string;
  is_correct: boolean;
  time_spent_seconds: number;

  // Hint usage
  hints_used: number; // 0-3
  hints_viewed: Hint[];

  // Evaluation
  evaluated_at: Date;
  confidence_level: 'low' | 'medium' | 'high'; // Based on hints needed
}

/**
 * Streak tracking
 */
export interface Streak {
  student_id: number;
  current_streak: number;
  longest_streak: number;
  last_practice_date: Date;
  milestones_achieved: number[]; // [7, 14, 30, ...]
  updated_at: Date;
}

/**
 * Cost tracking for API calls
 */
export interface CostRecord {
  cost_id: number;
  student_id: number;
  session_id: number;

  // Breakdown
  operation: 'hint_generation' | 'answer_evaluation';
  api_provider: 'claude' | 'twilio'; // Extensible

  // Cost metrics
  input_tokens?: number;
  output_tokens?: number;
  cost_usd: number;

  recorded_at: Date;
}
```

---

### 3.2 Problem Selection Algorithm

```typescript
/**
 * Select 5 problems for a student's daily practice session
 *
 * INTERFACE CONTRACT:
 * - Input: student's past performance
 * - Output: ordered list of 5 problem IDs
 * - Deterministic: same input → same output (for testing)
 * - Performance: <500ms
 */
export interface ProblemSelector {
  selectProblems(
    studentId: number,
    grade: 6 | 7 | 8,
    performanceHistory: PerformanceHistory
  ): Promise<ProblemSelection>;
}

/**
 * Student's historical performance data
 */
export interface PerformanceHistory {
  // Last N sessions (for trend analysis)
  recent_sessions: SessionSummary[];

  // Topic-level mastery
  topic_mastery: Map<string, TopicStats>;

  // Overall stats
  total_problems_attempted: number;
  overall_accuracy: number; // 0-100
  average_hints_per_problem: number;
}

export interface SessionSummary {
  session_id: number;
  date: Date;
  problems_correct: number;
  problems_attempted: number;
  accuracy: number; // 0-100
  topics_covered: string[];
}

export interface TopicStats {
  topic: string;
  problems_attempted: number;
  problems_correct: number;
  accuracy: number; // 0-100
  last_practiced: Date;
  mastery_level: 'novice' | 'developing' | 'proficient' | 'expert';
}

/**
 * Result of problem selection
 */
export interface ProblemSelection {
  selected_problem_ids: number[]; // Ordered 1-5 (easy to hard)
  selection_timestamp: Date;

  // Why these problems?
  reasoning: SelectionReasoning;
}

export interface SelectionReasoning {
  // Weights used (should sum to 100)
  topic_recency_weight: number; // 50%
  mastery_weight: number; // 30%
  difficulty_variation_weight: number; // 20%

  // For each selected problem
  selections: Array<{
    problem_id: number;
    topic: string;
    difficulty: 1 | 2 | 3;
    reason: string; // "Topic not practiced in 5 days", "Low accuracy (40%)", etc.
  }>;
}
```

---

### 3.3 Answer Evaluation

```typescript
/**
 * Evaluate if a student's answer is correct
 *
 * INTERFACE CONTRACT:
 * - Must handle: numeric answers, multiple choice, text (extensible)
 * - Performance: <100ms per evaluation
 * - Fault tolerance: graceful failure if evaluator crashes
 */
export interface AnswerEvaluator {
  evaluate(
    problem: Problem,
    studentAnswer: string,
    previousHintsCount: number
  ): Promise<EvaluationResult>;
}

/**
 * Result of answer evaluation
 */
export interface EvaluationResult {
  is_correct: boolean;

  // Feedback to student
  feedback_en: string;
  feedback_bn: string;

  // Metadata
  answer_format_valid: boolean;
  confidence: number; // 0-1 (how confident is evaluator)

  // For learning analytics
  student_understanding: 'novice' | 'developing' | 'proficient';
}

/**
 * Problem types (for type-specific evaluation)
 */
export type ProblemType = 'numeric' | 'multiple_choice' | 'text' | 'expression';

/**
 * Numeric problem specifics
 */
export interface NumericProblem extends Problem {
  type: 'numeric';
  answer_numeric: number;
  acceptable_tolerance_percent: number; // Default 5%
  units?: string; // Optional: 'rupees', 'meters', etc.
}

/**
 * Multiple choice problem specifics
 */
export interface MultipleChoiceProblem extends Problem {
  type: 'multiple_choice';
  choices: string[];
  correct_choice_index: number;
}
```

---

### 3.4 Streak Calculation

```typescript
/**
 * Track and calculate student streaks
 *
 * INTERFACE CONTRACT:
 * - Performance: <100ms per lookup/update
 * - Deterministic: streak based on UTC date boundary (12am UTC)
 * - Fault tolerance: handle timezone edge cases
 */
export interface StreakTracker {
  recordPractice(
    studentId: number,
    sessionDate: Date
  ): Promise<StreakUpdate>;

  getStreak(studentId: number): Promise<Streak>;

  getMilestones(studentId: number): Promise<MilestoneAchievement[]>;
}

/**
 * Result of recording a practice session
 */
export interface StreakUpdate {
  previous_streak: number;
  current_streak: number;
  streak_changed: boolean; // true if incremented or reset
  milestone_achieved?: number; // 7, 14, 30, etc.
  milestone_newly_achieved: boolean;
}

/**
 * Milestone achievement tracking
 */
export interface MilestoneAchievement {
  milestone_days: number; // 7, 14, 30
  achieved_at: Date;
  is_current: boolean; // True if streak currently active at this milestone
}
```

---

### 3.5 Hint Generation (Claude API)

```typescript
/**
 * Generate Socratic hints using Claude API
 *
 * INTERFACE CONTRACT:
 * - Performance: <3 seconds per hint (acceptable latency)
 * - Caching: hints for same problem_id+hint_number cached 7+ days
 * - Fallback: pre-written hints if API fails
 * - Cost: log every call for cost tracking
 */
export interface HintGenerator {
  generateHint(
    problem: Problem,
    studentAnswer: string,
    hintNumber: 1 | 2 | 3,
    language: 'en' | 'bn'
  ): Promise<GeneratedHint>;
}

/**
 * Generated hint response
 */
export interface GeneratedHint {
  hint_text: string;
  hint_number: 1 | 2 | 3;
  language: 'en' | 'bn';

  // Metadata
  source: 'claude_ai' | 'fallback_prewritten';
  generated_at: Date;
  cache_hit: boolean; // true if from cache

  // Cost tracking
  tokens_used?: {
    input: number;
    output: number;
  };
}

/**
 * Prompt template for Claude
 */
export const SOCRATIC_HINT_PROMPT = `
Problem: {problem_question}
Student's Answer: {student_answer}
Correct Answer: {correct_answer}
Hint Number: {hint_number}

Guide this student to the correct answer using the Socratic method.
- Hint 1: Start with a guiding question about the key concept
- Hint 2: Point out the specific misconception or missing step
- Hint 3: Give step-by-step guidance but do NOT give the answer

Generate Hint {hint_number} ONLY. No preamble. Just the hint text.
Make it conversational and encouraging.
`;
```

---

### 3.6 Cost Tracking

```typescript
/**
 * Track costs of operations for business model validation
 *
 * INTERFACE CONTRACT:
 * - Log EVERY external API call
 * - Calculate per-student cost for billing/analytics
 * - Alert if trends exceed budget
 */
export interface CostTracker {
  recordCost(
    studentId: number,
    operation: string,
    tokens?: TokenUsage,
    baseCost?: number
  ): Promise<void>;

  getCostSummary(
    period: 'day' | 'week' | 'month'
  ): Promise<CostSummary>;

  getPerStudentCost(studentId: number): Promise<number>;

  checkBudgetAlert(
    projectedMonthlyPerStudent: number,
    budgetLimit: number
  ): Promise<BudgetAlert | null>;
}

/**
 * Token usage from Claude API
 */
export interface TokenUsage {
  input_tokens: number;
  output_tokens: number;
}

/**
 * Cost summary for reporting
 */
export interface CostSummary {
  period: 'day' | 'week' | 'month';
  total_cost_usd: number;
  daily_average_usd: number;
  projected_monthly_usd: number;
  per_student_cost_usd: number;

  breakdown: CostBreakdown;
}

export interface CostBreakdown {
  claude_hints_cost: number;
  infrastructure_cost: number;
  other_cost: number;
}

/**
 * Budget alert
 */
export interface BudgetAlert {
  alert_type: 'warning' | 'critical';
  message: string;
  current_cost: number;
  budget_limit: number;
  projected_overage: number;
}
```

---

### 3.7 Telegram Message Handler

```typescript
/**
 * Process Telegram commands from students
 *
 * INTERFACE CONTRACT:
 * - Handle: /start, /practice, /streak, /help, /language, /hint, /admin
 * - Response: Send message back via Telegram API
 * - Idempotency: Handle duplicate updates gracefully
 */
export interface MessageHandler {
  handleMessage(
    update: TelegramUpdate
  ): Promise<void>;
}

/**
 * Command types
 */
export type Command =
  | 'start'      // /start
  | 'practice'   // /practice
  | 'streak'     // /streak
  | 'hint'       // /hint
  | 'help'       // /help
  | 'language'   // /language
  | 'answer'     // User submits answer
  | 'admin';     // /admin commands

/**
 * Message routing
 */
export interface CommandRouter {
  route(
    command: Command,
    studentId: number,
    payload?: string
  ): Promise<TelegramResponse>;
}

/**
 * Response to send back to student
 */
export interface TelegramResponse {
  message_text: string; // Message content
  parse_mode?: 'HTML' | 'Markdown'; // Formatting
  reply_markup?: InlineKeyboard; // Buttons if needed
}

/**
 * Inline keyboard (buttons)
 */
export interface InlineKeyboard {
  inline_keyboard: Array<Array<{
    text: string;
    callback_data: string; // Data to send back on button press
  }>>;
}
```

---

### 3.8 Session Management

```typescript
/**
 * Manage practice sessions (CRUD + state)
 *
 * INTERFACE CONTRACT:
 * - Create session, persist immediately
 * - Resume session if interrupted
 * - Auto-complete after 30 minutes
 * - Atomicity: all-or-nothing updates
 */
export interface SessionManager {
  createSession(
    studentId: number,
    problemIds: number[]
  ): Promise<Session>;

  resumeSession(
    studentId: number,
    sessionDate: Date
  ): Promise<Session | null>;

  recordResponse(
    sessionId: number,
    problemId: number,
    studentAnswer: string,
    hintsUsed: number
  ): Promise<Response>;

  completeSession(sessionId: number): Promise<Session>;

  getActiveSession(
    studentId: number
  ): Promise<Session | null>;
}

/**
 * Session state transitions
 */
export type SessionState =
  | 'not_started'
  | 'problem_1_of_5'
  | 'problem_2_of_5'
  | 'problem_3_of_5'
  | 'problem_4_of_5'
  | 'problem_5_of_5'
  | 'completed'
  | 'expired';

export interface SessionStateTransition {
  from_state: SessionState;
  to_state: SessionState;
  timestamp: Date;
  event: string; // 'answer_submitted', 'hint_requested', etc.
}
```

---

### 3.9 Learning Path Generator

```typescript
/**
 * Generate personalized learning path for student
 *
 * INTERFACE CONTRACT:
 * - Depends on: Answer evaluation data from current session
 * - Used by: Stream D (Learning), Stream B (Frontend dashboard)
 * - Performance: <500ms
 * - Returns: Topics for today, topics for next week, mastery summary
 */
export interface LearningPathGenerator {
  generateTodayPath(
    studentId: number,
    grade: 6 | 7 | 8,
    performanceData: PerformanceHistory
  ): Promise<DailyLearningPath>;

  generateWeekPath(
    studentId: number,
    grade: 6 | 7 | 8,
    performanceData: PerformanceHistory
  ): Promise<WeeklyLearningPath>;

  getMasterySnapshot(studentId: number): Promise<MasterySnapshot>;
}

/**
 * Daily learning path for a student
 */
export interface DailyLearningPath {
  date: Date;
  topics_today: TopicWithProgress[];
  focus_areas: string[]; // Areas needing work
  strength_areas: string[]; // Areas of confidence
  estimated_completion_time_minutes: number;
}

/**
 * Weekly learning path overview
 */
export interface WeeklyLearningPath {
  week_start: Date;
  topics_this_week: TopicWithProgress[];
  topics_next_week: TopicWithProgress[];
  projected_mastery_gains: Array<{
    topic: string;
    current_mastery: number; // 0-100
    projected_mastery: number; // 0-100
  }>;
}

/**
 * Snapshot of student's mastery across topics
 */
export interface MasterySnapshot {
  student_id: number;
  as_of: Date;
  overall_accuracy: number; // 0-100
  topics: Array<{
    topic: string;
    accuracy: number; // 0-100
    problems_attempted: number;
    mastery_level: 'novice' | 'developing' | 'proficient' | 'expert';
    last_practiced: Date;
  }>;
}

/**
 * Topic with progress metadata
 */
export interface TopicWithProgress {
  topic: string;
  difficulty_level: 1 | 2 | 3;
  mastery_percent: number; // 0-100
  problems_available: number;
  problems_completed: number;
  recommended_for_today: boolean;
}
```

---

### 3.10 Notification & Reminder Service

```typescript
/**
 * Send reminders and notifications to students
 *
 * INTERFACE CONTRACT:
 * - Used by: REQ-011 (Streak Reminders), REQ-013 (Encouragement)
 * - Performance: Non-blocking (queue-based delivery)
 * - Channels: Telegram (Phase 0), Email/SMS (Phase 1+)
 * - Scheduling: Cron jobs at fixed times (6pm IST for reminders)
 */
export interface NotificationService {
  sendReminder(
    studentId: number,
    reminderType: ReminderType,
    context?: Record<string, unknown>
  ): Promise<NotificationResult>;

  scheduleReminder(
    studentId: number,
    reminderType: ReminderType,
    scheduledTime: Date
  ): Promise<ScheduledReminder>;

  sendEncouragement(
    studentId: number,
    triggerEvent: EncouragementTrigger,
    data: EncouragementData
  ): Promise<NotificationResult>;

  getNotificationHistory(
    studentId: number,
    limit?: number
  ): Promise<NotificationRecord[]>;
}

/**
 * Types of reminders students can receive
 */
export type ReminderType =
  | 'daily_practice'     // "Time for your daily practice!"
  | 'streak_milestone'   // "You've reached 7 days! 🎉"
  | 'streak_at_risk'     // "Your 5-day streak is ending today"
  | 'return_after_gap';  // "We miss you! Come back and practice"

/**
 * Triggers for encouragement messages
 */
export type EncouragementTrigger =
  | 'correct_answer'     // After solving a problem
  | 'streak_achieved'    // Reached 3-day, 7-day, 14-day, 30-day
  | 'mastery_milestone'  // Achieved proficiency in a topic
  | 'hints_used_well';   // Used hints effectively to learn

/**
 * Context for encouragement messages
 */
export interface EncouragementData {
  student_name: string;
  current_streak?: number;
  problems_correct_today?: number;
  mastered_topic?: string;
  accuracy_percent?: number;
}

/**
 * Result of sending notification
 */
export interface NotificationResult {
  notification_id: string;
  student_id: number;
  message_text: string;
  sent_at: Date;
  delivery_status: 'queued' | 'sent' | 'failed';
  error_details?: string;
}

/**
 * Scheduled reminder record
 */
export interface ScheduledReminder {
  reminder_id: string;
  student_id: number;
  reminder_type: ReminderType;
  scheduled_for: Date;
  status: 'scheduled' | 'sent' | 'cancelled';
  created_at: Date;
}

/**
 * Historical record of notifications sent
 */
export interface NotificationRecord {
  notification_id: string;
  reminder_type: ReminderType;
  message_text: string;
  sent_at: Date;
  delivery_channel: 'telegram' | 'email' | 'sms';
  delivery_status: 'sent' | 'failed';
}
```

---

### 3.11 Localization & Translation Service

```typescript
/**
 * Handle message localization (Bengali + English)
 *
 * INTERFACE CONTRACT:
 * - Used by: Stream D (all UI messages), Stream E (admin messages)
 * - Performance: <50ms per translation lookup (in-memory cache)
 * - Coverage: 100% of user-facing strings in both Bengali & English
 * - Extensible: Support for additional languages in Phase 1+
 */
export interface LocalizationService {
  getMessage(
    messageKey: string,
    language: 'en' | 'bn',
    params?: Record<string, string | number>
  ): string;

  getMessageSet(
    messageKeys: string[],
    language: 'en' | 'bn'
  ): Record<string, string>;

  formatNumber(
    value: number,
    language: 'en' | 'bn',
    options?: Intl.NumberFormatOptions
  ): string;

  formatDate(
    date: Date,
    language: 'en' | 'bn',
    format?: 'short' | 'medium' | 'long'
  ): string;
}

/**
 * Message key constants
 * Format: CATEGORY_SUBCATEGORY_ACTION
 */
export enum MessageKey {
  // Greetings
  GREETING_START = 'GREETING_START', // "Welcome to Dars!"
  GREETING_RETURN = 'GREETING_RETURN', // "Welcome back, {name}!"

  // Practice session
  PRACTICE_READY = 'PRACTICE_READY', // "Ready for today's challenge?"
  PRACTICE_PROBLEM_X_OF_5 = 'PRACTICE_PROBLEM_X_OF_5', // "Problem {n} of 5"
  PRACTICE_CORRECT = 'PRACTICE_CORRECT', // "Correct! Well done!"
  PRACTICE_INCORRECT = 'PRACTICE_INCORRECT', // "Not quite. Try again or ask for a hint."
  PRACTICE_COMPLETED = 'PRACTICE_COMPLETED', // "You completed today's practice!"

  // Hints
  HINT_LEVEL_1 = 'HINT_LEVEL_1', // "Think about..."
  HINT_LEVEL_2 = 'HINT_LEVEL_2', // "You might have missed..."
  HINT_LEVEL_3 = 'HINT_LEVEL_3', // "Here's how to solve it step by step..."
  HINT_EXHAUSTED = 'HINT_EXHAUSTED', // "No more hints available"

  // Streaks
  STREAK_MILESTONE_7 = 'STREAK_MILESTONE_7', // "7-day streak! 🎉"
  STREAK_MILESTONE_14 = 'STREAK_MILESTONE_14', // "14-day streak! 🔥"
  STREAK_MILESTONE_30 = 'STREAK_MILESTONE_30', // "30-day streak! ⭐"
  STREAK_AT_RISK = 'STREAK_AT_RISK', // "Your streak ends today..."

  // Errors
  ERROR_SESSION_EXPIRED = 'ERROR_SESSION_EXPIRED', // "Session expired"
  ERROR_INVALID_ANSWER = 'ERROR_INVALID_ANSWER', // "Please enter a valid answer"
  ERROR_STUDENT_NOT_FOUND = 'ERROR_STUDENT_NOT_FOUND', // "Student not found"
}

/**
 * Localization resources
 * Loaded at startup, cached in memory
 */
export interface LocalizationResources {
  en: Record<string, string>;
  bn: Record<string, string>;
}

/**
 * Message template with parameter interpolation
 * Example: "Hello {name}, you got {correct} out of {total} correct!"
 */
export interface MessageTemplate {
  key: string;
  template: string;
  parameters: string[]; // Variable names
  language: 'en' | 'bn';
}
```

---

# PART 3B: WORK STREAM OWNERSHIP & HANDOFF COORDINATION

This section maps all endpoints, service contracts, and dependencies to work streams to enable parallel development.

## Stream A: Backend Infrastructure (REQ-017, 018, 020, 019, 031)
**Owner:** 3-4 agents (Database, API, Error Handling, Security, Health Check)
**Deliverable:** Working FastAPI backend serving all components

### Endpoints Owned:
- `POST /webhook` - Telegram webhook (receives updates)
- `GET /health` - System health check
- `GET /admin/*` - All admin endpoints
- `GET/PATCH /practice/*` - Practice flow endpoints
- `GET /streak` - Streak data endpoint
- `GET/PATCH /student/profile` - Student profile endpoint

### Service Contracts Owned:
- `SessionManager` - Practice session CRUD & state
- `CostTracker` - Cost recording & tracking
- All database models and migrations

### Handoff Points (to other streams):
1. **Day 2 → Stream D:** Database schema ready, connection string provided
2. **Day 3 → Stream D:** FastAPI app structure + OpenAPI docs at `/docs`
3. **Day 5 → Stream D:** All endpoints stubbed and responding
4. **Day 3 → Stream C:** Database import capability for content

### Success Criteria:
- ✅ `pytest tests/integration/test_db.py` passes
- ✅ `curl http://localhost:8000/health` returns 200 with db+claude status
- ✅ All endpoints appear in `GET http://localhost:8000/docs`
- ✅ Admin auth works (X-Admin-ID header validation)
- ✅ Structured JSON logging in place

---

## Stream C: Content & Localization (REQ-005, 022, 023, 021)
**Owner:** 1-2 agents + 1 human (content curation + Bengali speaker)
**Deliverable:** 280 verified problems + translations + curriculum mapping

### Service Contracts Owned:
- `LocalizationService` - Message translation (en/bn)
- All message templates and strings

### Data Owned:
- Problem library (280 problems minimum)
- Curriculum mapping document
- Bengali translations (reviewed)
- Cultural appropriateness checklist

### Dependencies:
- Requires: Stream A database ready (by day 2)
- Provides: Problem data to Stream D (by day 10)

### Handoff Points:
1. **Day 10 → Stream D:** 280 problems in database + CSV backup
   - Format: Import via `/admin/import-problems` or direct SQL
   - Verification: `SELECT COUNT(*) FROM problems` = 280
2. **Day 10 → Stream A:** Curriculum mapping doc for admin dashboard
3. **Day 21 → Stream D:** All UI strings ready for translation
   - Format: YAML file with message keys → en/bn translations
   - Verification: 100% coverage of MessageKey enum

### Success Criteria:
- ✅ 280 problems in database
- ✅ Each problem: id, grade, topic, question_en, question_bn, answer, hints[3], difficulty
- ✅ All Bengali reviewed by native speaker
- ✅ No duplicates
- ✅ Curriculum mapping created
- ✅ Cultural appropriateness verified

---

## Stream D: Learning Algorithm & Engagement (REQ-001, 008, 003, 007, 004, 006, 015, 016, 002, 009, 010, 012, 013, 011)
**Owner:** 2-3 agents (Learning engine, algorithms, engagement)
**Deliverable:** Complete learning experience with hints & gamification

### Service Contracts Owned:
- `ProblemSelector` - Intelligent problem selection algorithm
- `AnswerEvaluator` - Answer evaluation with type handling
- `AdaptiveDifficulty` - Dynamic difficulty adjustment (modifier to ProblemSelector)
- `HintGenerator` - Claude-powered Socratic hints
- `StreakTracker` - Habit tracking with milestones
- `LearningPathGenerator` - Personalized learning paths
- `NotificationService` - Reminders & encouragement messages

### Endpoints Used (not owned, but implemented against):
- `GET /practice` - Returns 5 selected problems
- `POST /practice/{problem_id}/answer` - Submits answer & gets evaluation
- `POST /practice/{problem_id}/hint` - Requests Socratic hint
- `GET /streak` - Displays streak information
- `GET /student/profile` - Gets student learning history

### Handoff Points:
1. **Receive (Day 2):** Stream A provides database schema
2. **Receive (Day 3):** Stream A provides API endpoints stubbed
3. **Receive (Day 10):** Stream C provides 280 problems in database
4. **Day 13 → Next phase:** Selection algorithm complete + tested
   - Format: `selectProblems(studentId, grade, performanceHistory) → ProblemSelection`
   - Verification: `pytest tests/unit/test_selection.py` passes
5. **Day 15 → Next phase:** Practice flow complete
   - Format: `/practice` returns 5 problem IDs, `/practice/{id}/answer` evaluates
   - Verification: Manual test: submit 5 answers → all evaluated correctly
6. **Day 17 → Next phase:** Claude hints working
   - Format: `generateHint()` returns 3-level Socratic hint
   - Verification: Manual test: hint generation <3 seconds, cache hit rate >70%
7. **Day 21 → Stream C:** Ready for localization
   - Format: Provide list of all UI message keys needing translation
8. **Day 22 → Stream E:** Engagement features ready
   - Format: Streak data in database, notification events triggerable

### Success Criteria:
- ✅ Selection algorithm deterministic (same input → same output)
- ✅ Answer evaluation handles numeric (±5%), MC (exact), future text types
- ✅ Difficulty adapts: +1 level on 2 correct, -1 level on 1 incorrect
- ✅ Learning path shows topics for today + next week
- ✅ Claude hints generate in <3 seconds
- ✅ Hint caching achieves 70%+ hit rate
- ✅ Hints cached cost <$0.001 each
- ✅ Streak increments on daily practice
- ✅ Milestones celebrated at 7, 14, 30 days

---

## Stream E: Operations & Monitoring (REQ-029, 030, 032, 033)
**Owner:** 1-2 agents (Cost tracking, deployment, monitoring)
**Deliverable:** Production deployment with cost visibility

### Service Contracts Owned:
- Cost aggregation and reporting via API

### Endpoints Used (not owned):
- `GET /admin/cost` - Cost summary
- `GET /admin/stats` - System statistics

### Dependencies:
- Requires: Stream A logging infrastructure (day 3)
- Requires: Stream D cost data (day 22)
- Requires: Stream B admin UI (day 35)

### Handoff Points:
1. **Day 29 → Stream B:** Cost tracking API ready
   - Format: `GET /admin/cost?period=week` returns CostSummary
2. **Day 35 → Stream B:** Deployment complete
   - Format: Service running at https://dars.railway.app
   - Verification: Health check passes, logs aggregated

### Success Criteria:
- ✅ Every Claude call logged with tokens
- ✅ `/admin/cost` shows daily/weekly/monthly breakdown
- ✅ Per-student cost calculated
- ✅ Alert triggered if >$0.15/month projected
- ✅ Deployed to Railway successfully
- ✅ Backups automated
- ✅ Health checks passing

---

## Stream B: Frontend & Admin UI (REQ-034)
**Owner:** 1 agent (Admin dashboard)
**Deliverable:** Admin web interface with analytics

### Endpoints Used (not owned):
- `GET /admin/stats` - Statistics
- `GET /admin/students` - Student list
- `GET /admin/cost` - Cost data

### Dependencies:
- Requires: Stream A API ready (day 3)
- Requires: Stream E cost tracking (day 29)

### Handoff Points:
1. **Day 35 → Deployment:** Dashboard code ready
   - Format: HTML/CSS/JS files for admin interface
   - Verification: All metrics display correctly with live data

### Success Criteria:
- ✅ Dashboard displays: students, engagement, costs
- ✅ Real-time data refresh (30s intervals)
- ✅ Responsive design (mobile + desktop)
- ✅ SSL/HTTPS working
- ✅ Admin auth enforced

---

## Integration Checklist

| Day | Handoff | From → To | What | Verification |
|-----|---------|-----------|------|--------------|
| 2 | Database | A → All | Schema, models | `pytest test_db.py` ✓ |
| 3 | API | A → D,E,B | Endpoints, OpenAPI | `GET /docs` shows routes ✓ |
| 5 | Security | A → All | Auth, error handling | Admin token works ✓ |
| 10 | Content | C → D | 280 problems | `SELECT COUNT(*)` = 280 ✓ |
| 13 | Selection | D → Integration | Algorithm | `pytest test_selection.py` ✓ |
| 15 | Practice Flow | D → Integration | Sessions, answers | Manual: 5 problems → evaluated ✓ |
| 17 | Hints | D → Integration | Claude integration | Manual: hint generation works ✓ |
| 21 | Strings | C → D | Localization file | All message keys translated ✓ |
| 22 | Engagement | D → E,B | Streaks, notifications | Streaks increment ✓ |
| 29 | Cost API | E → B | Cost endpoint | `/admin/cost` returns data ✓ |
| 35 | Dashboard | B → Deployment | Admin UI | Dashboard accessible ✓ |
| 35 | Deployment | E → Launch | Live system | Health check passes ✓ |

---

# PART 4: ERROR HANDLING STANDARDS

## Error Response Format

All errors follow this standard format:

```typescript
/**
 * Standard error response
 */
export interface ApiError {
  error: ErrorType;
  message: string;
  error_code: string;
  details?: Record<string, unknown>;
  timestamp: Date;
  request_id: string;
}

export type ErrorType =
  | 'bad_request'        // 400: Invalid input
  | 'unauthorized'       // 401: Auth failed
  | 'forbidden'          // 403: Not permitted
  | 'not_found'          // 404: Resource not found
  | 'conflict'           // 409: State conflict
  | 'internal_error'     // 500: Server error
  | 'service_unavailable'; // 503: Dependency down

/**
 * Common error codes
 */
export enum ErrorCode {
  // Auth errors
  ERR_AUTH_FAILED = 'ERR_AUTH_FAILED',
  ERR_AUTH_MISSING = 'ERR_AUTH_MISSING',
  ERR_ADMIN_ONLY = 'ERR_ADMIN_ONLY',

  // Validation errors
  ERR_INVALID_JSON = 'ERR_INVALID_JSON',
  ERR_INVALID_PARAM = 'ERR_INVALID_PARAM',
  ERR_INVALID_GRADE = 'ERR_INVALID_GRADE',
  ERR_INVALID_LANGUAGE = 'ERR_INVALID_LANGUAGE',

  // Resource errors
  ERR_STUDENT_NOT_FOUND = 'ERR_STUDENT_NOT_FOUND',
  ERR_PROBLEM_NOT_FOUND = 'ERR_PROBLEM_NOT_FOUND',
  ERR_SESSION_NOT_FOUND = 'ERR_SESSION_NOT_FOUND',
  ERR_SESSION_EXPIRED = 'ERR_SESSION_EXPIRED',

  // State errors
  ERR_SESSION_ALREADY_ACTIVE = 'ERR_SESSION_ALREADY_ACTIVE',
  ERR_SESSION_ALREADY_COMPLETED = 'ERR_SESSION_ALREADY_COMPLETED',
  ERR_DUPLICATE_RESPONSE = 'ERR_DUPLICATE_RESPONSE',

  // External service errors
  ERR_CLAUDE_API_FAILED = 'ERR_CLAUDE_API_FAILED',
  ERR_CLAUDE_TIMEOUT = 'ERR_CLAUDE_TIMEOUT',
  ERR_TELEGRAM_API_FAILED = 'ERR_TELEGRAM_API_FAILED',
  ERR_DATABASE_ERROR = 'ERR_DATABASE_ERROR',

  // Internal errors
  ERR_INTERNAL = 'ERR_INTERNAL',
}

/**
 * Example error responses
 */

// Bad request
const badRequestError: ApiError = {
  error: 'bad_request',
  message: 'Student grade must be 6, 7, or 8',
  error_code: ErrorCode.ERR_INVALID_GRADE,
  details: {
    provided_grade: 10,
    valid_grades: [6, 7, 8],
  },
  timestamp: new Date(),
  request_id: 'req_123456789',
};

// Unauthorized
const unauthorizedError: ApiError = {
  error: 'unauthorized',
  message: 'Invalid authentication token',
  error_code: ErrorCode.ERR_AUTH_FAILED,
  timestamp: new Date(),
  request_id: 'req_123456789',
};

// Service unavailable
const serviceUnavailableError: ApiError = {
  error: 'service_unavailable',
  message: 'Claude API is currently unavailable',
  error_code: ErrorCode.ERR_CLAUDE_TIMEOUT,
  details: {
    retry_after_seconds: 30,
  },
  timestamp: new Date(),
  request_id: 'req_123456789',
};
```

---

## Error Handling Strategy

```typescript
/**
 * Error handling guidelines for services
 */

// 1. CATCH SPECIFIC ERRORS
try {
  const hint = await generateHint(problem, answer, hintNumber);
} catch (error) {
  if (error instanceof TimeoutError) {
    // Expected: API timeout, use fallback
    return getFallbackHint(problem, hintNumber);
  } else if (error instanceof ValidationError) {
    // Expected: invalid input
    throw new ApiError('bad_request', error.message);
  } else {
    // Unexpected: log and return generic error
    logger.error('Unexpected error in hint generation', { error });
    throw new ApiError('internal_error', 'Something went wrong');
  }
}

// 2. ALWAYS HAVE FALLBACKS
const hint = await generateHintWithFallback(
  problem,
  hintNumber,
  async () => await generateHintViaClaudeAPI(...),
  () => getFallbackPrewrittenHint(problem, hintNumber)
);

// 3. LOG ERRORS WITH CONTEXT
logger.error('Claude API call failed', {
  problem_id: problem.id,
  hint_number: hintNumber,
  error_code: error.code,
  retry_count: retries,
  request_id: generateRequestId(),
});

// 4. FAIL SAFELY
// Never crash the app. Return error response instead.
app.get('/admin/cost', async (req, res) => {
  try {
    const cost = await getCostSummary();
    res.json(cost);
  } catch (error) {
    // Return error, not crash
    res.status(500).json({
      error: 'internal_error',
      message: 'Could not retrieve cost data',
      request_id: req.id,
    });
  }
});
```

---

# PART 5: AUTHENTICATION & SECURITY

## Authentication Schemes

### 5.1 Telegram Webhook Authentication

```typescript
/**
 * Authenticate Telegram webhook using bot token
 *
 * Telegram sends updates to /webhook
 * We verify the Authorization header contains the bot token
 */

export interface TelegramAuth {
  // Every POST /webhook must include:
  // Authorization: Bearer YOUR_BOT_TOKEN

  verifyWebhookToken(token: string): boolean;
}

// Implementation
export function verifyWebhookToken(providedToken: string): boolean {
  const expectedToken = process.env.TELEGRAM_BOT_TOKEN;
  return providedToken === expectedToken;
}

// Middleware
export function telegramAuthMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
) {
  const authHeader = req.headers.authorization;
  if (!authHeader) {
    return res.status(401).json({
      error: 'unauthorized',
      message: 'Missing Authorization header',
      error_code: 'ERR_AUTH_MISSING',
    });
  }

  const token = authHeader.replace('Bearer ', '');
  if (!verifyWebhookToken(token)) {
    return res.status(401).json({
      error: 'unauthorized',
      message: 'Invalid token',
      error_code: 'ERR_AUTH_FAILED',
    });
  }

  next();
}
```

### 5.2 Admin Authentication (Phase 0)

```typescript
/**
 * Phase 0: Hardcoded admin Telegram IDs
 * Phase 1: JWT tokens
 */

export interface AdminAuth {
  // Phase 0: Check if user is in admin list
  isAdmin(telegramId: number): boolean;

  // Phase 1: Validate JWT token
  validateToken(token: string): Promise<AdminUser>;
}

// Phase 0 Implementation
const ADMIN_TELEGRAM_IDS = [
  123456789, // Product manager
  987654321, // Tech lead
];

export function isAdmin(telegramId: number): boolean {
  return ADMIN_TELEGRAM_IDS.includes(telegramId);
}

// Middleware for Phase 0
export function adminAuthMiddlewarePhase0(
  req: Request,
  res: Response,
  next: NextFunction
) {
  const adminId = req.headers['x-admin-id'] as string;

  if (!adminId || !isAdmin(parseInt(adminId))) {
    return res.status(403).json({
      error: 'forbidden',
      message: 'Only admins can access this endpoint',
      error_code: 'ERR_ADMIN_ONLY',
    });
  }

  next();
}

// Phase 1: JWT tokens
export interface AdminUser {
  telegram_id: number;
  name: string;
  email: string;
  role: 'admin' | 'manager';
}

export async function validateJWTToken(token: string): Promise<AdminUser> {
  // Implemented in Phase 1
  // For now, just parse the token
}
```

### 5.3 Rate Limiting

```typescript
/**
 * Rate limiting to prevent abuse
 */

export interface RateLimiter {
  // Limit API calls per IP per minute
  checkRateLimit(
    ip: string,
    limit: number,
    windowSeconds: number
  ): Promise<RateLimitResult>;
}

export interface RateLimitResult {
  allowed: boolean;
  remaining: number;
  reset_at: Date;
}

// Example: 100 requests per minute per IP
app.use((req, res, next) => {
  const ip = req.ip;
  const limit = 100;
  const windowSeconds = 60;

  rateLimiter.checkRateLimit(ip, limit, windowSeconds)
    .then(result => {
      res.setHeader('X-RateLimit-Remaining', result.remaining);
      res.setHeader('X-RateLimit-Reset', result.reset_at.toISOString());

      if (!result.allowed) {
        return res.status(429).json({
          error: 'too_many_requests',
          message: 'Rate limit exceeded',
          retry_after: Math.ceil(
            (result.reset_at.getTime() - Date.now()) / 1000
          ),
        });
      }

      next();
    });
});
```

### 5.4 Secret Management

```typescript
/**
 * Never hardcode secrets. Use environment variables.
 */

// ✅ CORRECT
const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const CLAUDE_API_KEY = process.env.ANTHROPIC_API_KEY;
const DATABASE_URL = process.env.DATABASE_URL;

// ❌ WRONG - NEVER DO THIS
const secrets = {
  telegram_token: 'YOUR_TOKEN_HERE',
  claude_key: 'YOUR_KEY_HERE',
};

// Environment variables to configure
export interface RequiredEnvVars {
  TELEGRAM_BOT_TOKEN: string;
  ANTHROPIC_API_KEY: string;
  DATABASE_URL: string;
  ADMIN_TELEGRAM_IDS: string; // Comma-separated
  NODE_ENV: 'development' | 'staging' | 'production';
}

// Validation
export function validateEnvVars(): void {
  const required: (keyof RequiredEnvVars)[] = [
    'TELEGRAM_BOT_TOKEN',
    'ANTHROPIC_API_KEY',
    'DATABASE_URL',
  ];

  for (const key of required) {
    if (!process.env[key]) {
      throw new Error(`Missing required environment variable: ${key}`);
    }
  }
}
```

---

# PART 6: REQUEST/RESPONSE EXAMPLES

## 6.1 Telegram Webhook Examples

### /start Command

```json
// REQUEST
{
  "update_id": 123456789,
  "message": {
    "message_id": 1,
    "date": 1643129200,
    "chat": {
      "id": 987654321,
      "type": "private"
    },
    "from": {
      "id": 987654321,
      "is_bot": false,
      "first_name": "Rajesh"
    },
    "text": "/start"
  }
}

// RESPONSE (sent to Telegram)
{
  "chat_id": 987654321,
  "text": "শুভস্বাগতম! আমি Dars, আপনার এআই গণিত শিক্ষক। প্রতিদিন ৫টি সমস্যা সমাধান করে আপনার দক্ষতা বৃদ্ধি করুন।\n\nভাষা বেছে নিন: Bengali / English?",
  "reply_markup": {
    "inline_keyboard": [[
      {
        "text": "Bengali (বাংলা)",
        "callback_data": "lang_bn"
      },
      {
        "text": "English",
        "callback_data": "lang_en"
      }
    ]]
  }
}
```

### /practice Command

```json
// REQUEST
{
  "update_id": 123456790,
  "message": {
    "message_id": 5,
    "date": 1643129500,
    "chat": {
      "id": 987654321,
      "type": "private"
    },
    "from": {
      "id": 987654321,
      "is_bot": false,
      "first_name": "Rajesh"
    },
    "text": "/practice"
  }
}

// RESPONSE (sent to Telegram)
{
  "chat_id": 987654321,
  "text": "Problem 1 of 5 - Difficulty: Easy\n\nএক দোকানদার 15টি আম ₹300 এর জন্য ক্রয় করেন। তিনি প্রতিটি আম ₹25 এ বিক্রয় করেন। তার লাভ কত?\n\nA) ₹75\nB) ₹100\nC) ₹125\nD) ₹150",
  "reply_markup": {
    "inline_keyboard": [[
      {
        "text": "A) ₹75",
        "callback_data": "answer_1_0"
      },
      {
        "text": "B) ₹100",
        "callback_data": "answer_1_1"
      }
    ], [
      {
        "text": "C) ₹125",
        "callback_data": "answer_1_2"
      },
      {
        "text": "D) ₹150",
        "callback_data": "answer_1_3"
      }
    ], [
      {
        "text": "💡 Hint",
        "callback_data": "hint_1"
      }
    ]]
  }
}
```

### Hint Request

```json
// REQUEST
{
  "update_id": 123456791,
  "callback_query": {
    "id": "callback_id_123",
    "from": {
      "id": 987654321,
      "is_bot": false,
      "first_name": "Rajesh"
    },
    "data": "hint_1"
  }
}

// RESPONSE (sent to Telegram)
{
  "chat_id": 987654321,
  "text": "💡 Hint 1 of 3:\n\nপ্রথমে, প্রতিটি আমের খরচ কত তা বের করুন।\n₹300 ÷ 15 = ?",
  "reply_markup": {
    "inline_keyboard": [[
      {
        "text": "A) ₹75",
        "callback_data": "answer_1_0"
      },
      {
        "text": "B) ₹100",
        "callback_data": "answer_1_1"
      }
    ], [
      {
        "text": "💡 Another Hint",
        "callback_data": "hint_1_2"
      }
    ]]
  }
}
```

---

## 6.2 Admin API Examples

### GET /admin/stats

```json
// REQUEST
GET /admin/stats
Authorization: Bearer YOUR_BOT_TOKEN
X-Admin-ID: 123456789

// RESPONSE 200 OK
{
  "total_students": 50,
  "active_this_week": 42,
  "active_this_week_percent": 84,
  "avg_streak": 7.2,
  "avg_problems_per_session": 4.8,
  "total_sessions": 342,
  "timestamp": "2026-01-28T10:30:00Z"
}

// RESPONSE 401 UNAUTHORIZED
{
  "error": "unauthorized",
  "message": "Invalid or missing authentication token",
  "error_code": "ERR_AUTH_FAILED",
  "timestamp": "2026-01-28T10:30:00Z",
  "request_id": "req_123456789"
}

// RESPONSE 403 FORBIDDEN
{
  "error": "forbidden",
  "message": "Only admins can access this endpoint",
  "error_code": "ERR_ADMIN_ONLY",
  "timestamp": "2026-01-28T10:30:00Z",
  "request_id": "req_123456789"
}
```

### GET /admin/cost

```json
// REQUEST
GET /admin/cost?period=week
Authorization: Bearer YOUR_BOT_TOKEN
X-Admin-ID: 123456789

// RESPONSE 200 OK
{
  "period": "week",
  "total_cost": 1.23,
  "daily_average": 0.18,
  "projected_monthly": 7.80,
  "per_student_cost": 0.16,
  "claude_cost": 1.10,
  "infrastructure_cost": 0.13,
  "alert": true,
  "alert_message": "Over budget - exceeds $0.15/student/month",
  "timestamp": "2026-01-28T10:30:00Z"
}
```

---

# PART 7: IMPLEMENTATION CHECKLIST

## Before Implementation Starts

- [ ] All team members review and approve API spec
- [ ] Confirm all endpoint paths and methods match requirements
- [ ] Verify request/response schema examples are realistic
- [ ] Confirm authentication approach (Telegram token, admin IDs)
- [ ] Decide on error code naming convention
- [ ] Verify database schema supports API contracts
- [ ] Create mock API for frontend to test against
- [ ] Create API documentation site (via OpenAPI tools)

## During Implementation

- [ ] Generate code from OpenAPI spec (optional, time-saver)
- [ ] Implement error handling per spec
- [ ] Add request validation middleware
- [ ] Add authentication middleware
- [ ] Add rate limiting middleware
- [ ] Implement logging for all API calls
- [ ] Test each endpoint with example payloads
- [ ] Write integration tests for each endpoint
- [ ] Verify error codes match spec
- [ ] Document any deviations from spec

## After Implementation

- [ ] All endpoints match OpenAPI spec exactly
- [ ] All error responses follow standard format
- [ ] Authentication works for all protected endpoints
- [ ] Rate limiting prevents abuse
- [ ] Logging includes request_id for tracing
- [ ] API documentation is auto-generated and up-to-date
- [ ] Teams are using correct request/response formats

---

## Checklist for Service Contracts

### Problem Selection Algorithm
- [ ] Input signature matches: `(studentId, grade, performanceHistory)`
- [ ] Output is ordered array of 5 problem IDs
- [ ] Performance: <500ms
- [ ] Deterministic: same input → same output
- [ ] Handles edge case: new student (all topics)
- [ ] Handles edge case: all topics mastered
- [ ] Weights correctly implemented: 50/30/20

### Answer Evaluation
- [ ] Handles numeric answers with tolerance
- [ ] Handles multiple choice (exact match)
- [ ] Handles text answers (future: semantic)
- [ ] Performance: <100ms
- [ ] Feedback in both English and Bengali
- [ ] Confidence level calculated

### Streak Tracking
- [ ] Increments on daily practice
- [ ] Resets on missed day
- [ ] Longest streak tracked separately
- [ ] Handles timezone edge cases
- [ ] Milestones recorded at 7, 14, 30 days

### Hint Generation
- [ ] Socratic method (no direct answers)
- [ ] Three hint levels (guiding → directing → guiding without answer)
- [ ] Caching works: 70%+ hit rate
- [ ] Fallback if API fails
- [ ] Cost tracking per hint

### Session Management
- [ ] Creates session atomically
- [ ] Persists immediately to database
- [ ] Resumes if disconnected
- [ ] Auto-completes after 30 minutes
- [ ] Prevents re-answering completed problems

---

## Sign-Off

This API Architecture specification is approved by:

- [ ] Backend Lead
- [ ] Frontend Lead (if applicable)
- [ ] Database Architect
- [ ] Product Manager
- [ ] Security Lead

Approved on: ___________

Version: 1.0
Status: READY FOR IMPLEMENTATION
