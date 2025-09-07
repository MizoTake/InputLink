# Requirements Document

## Introduction

This feature enables forwarding controller inputs from a sender PC to a receiver PC over a local network via WebSocket. The sender PC captures controller inputs (supporting both DInput and XInput), assigns controller numbers (1st controller, 2nd controller, etc.), and transmits this data to the receiver PC. The receiver PC then simulates these inputs at the driver level using tools like ViGEmBus, making the system believe the controllers are physically connected to the receiver PC. The solution must work on both Windows and Mac platforms.

## Requirements

### Requirement 1

**User Story:** As a user, I want to connect physical controllers to a sender PC and have them recognized with configurable controller numbers, so that I can organize multiple controllers for network forwarding.

#### Acceptance Criteria

1. WHEN a controller is connected to the sender PC THEN the system SHALL detect and list the controller
2. WHEN multiple controllers are connected THEN the system SHALL allow assignment of controller numbers (1st, 2nd, etc.)
3. WHEN a controller supports both DInput and XInput THEN the system SHALL allow selection of the preferred input method
4. WHEN controller configuration is changed THEN the system SHALL save the configuration for future sessions

### Requirement 2

**User Story:** As a user, I want the sender PC to capture all controller inputs in real-time, so that every button press, stick movement, and trigger action is recorded for transmission.

#### Acceptance Criteria

1. WHEN a controller button is pressed THEN the system SHALL capture the input with timestamp
2. WHEN analog sticks or triggers are moved THEN the system SHALL capture the precise analog values
3. WHEN multiple controllers are active simultaneously THEN the system SHALL capture inputs from all controllers independently
4. WHEN input polling occurs THEN the system SHALL maintain consistent polling rate for smooth input capture

### Requirement 3

**User Story:** As a user, I want controller input data to be transmitted over WebSocket to a receiver PC, so that the inputs can be processed remotely with minimal latency.

#### Acceptance Criteria

1. WHEN controller input is captured THEN the system SHALL format the data with controller number and input details
2. WHEN WebSocket connection is established THEN the system SHALL transmit input data in real-time
3. WHEN network connection is lost THEN the system SHALL attempt automatic reconnection
4. WHEN multiple controller inputs occur simultaneously THEN the system SHALL maintain input order and timing

### Requirement 4

**User Story:** As a user, I want the receiver PC to simulate the received controller inputs at driver level, so that applications believe physical controllers are connected locally.

#### Acceptance Criteria

1. WHEN input data is received via WebSocket THEN the system SHALL parse controller number and input details
2. WHEN parsed input data is valid THEN the system SHALL simulate the input using driver-level tools
3. WHEN multiple virtual controllers are needed THEN the system SHALL create and manage separate virtual controller instances
4. WHEN input simulation occurs THEN applications SHALL recognize the virtual controllers as physical devices

### Requirement 5

**User Story:** As a user, I want the system to work on both Windows and Mac platforms, so that I can use it regardless of my operating system choice.

#### Acceptance Criteria

1. WHEN running on Windows THEN the system SHALL use appropriate Windows APIs for controller input and ViGEmBus for output simulation
2. WHEN running on Mac THEN the system SHALL use appropriate macOS APIs for controller input and compatible virtual controller solutions
3. WHEN cross-platform communication occurs THEN WebSocket protocol SHALL work identically on both platforms
4. IF platform-specific features are unavailable THEN the system SHALL provide clear error messages and fallback options

### Requirement 6

**User Story:** As a user, I want a simple configuration interface to set up sender and receiver connections, so that I can easily establish the network link between PCs.

#### Acceptance Criteria

1. WHEN configuring the sender THEN the system SHALL allow specification of receiver PC IP address and port
2. WHEN configuring the receiver THEN the system SHALL allow specification of listening port and connection settings
3. WHEN connection is established THEN the system SHALL display connection status and active controller count
4. WHEN configuration is saved THEN the system SHALL remember settings for future sessions

### Requirement 7

**User Story:** As a user, I want the system to handle connection errors gracefully, so that temporary network issues don't crash the application.

#### Acceptance Criteria

1. WHEN WebSocket connection fails THEN the system SHALL display appropriate error messages
2. WHEN connection is lost during operation THEN the system SHALL attempt automatic reconnection with exponential backoff
3. WHEN receiver PC is unreachable THEN the sender SHALL continue capturing inputs and queue them for transmission
4. WHEN connection is restored THEN the system SHALL resume normal operation without requiring restart