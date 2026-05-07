DROP DATABASE IF EXISTS authvote;
CREATE DATABASE authvote;
USE authvote;

CREATE TABLE ElectionState (
    id INT PRIMARY KEY DEFAULT 1,
    state ENUM('PENDING', 'ACTIVE', 'ENDED') DEFAULT 'PENDING'
);
INSERT INTO ElectionState (id, state) VALUES (1, 'PENDING');

CREATE TABLE VoterRegistry (
    voter_id INT AUTO_INCREMENT PRIMARY KEY,
    prn VARCHAR(20) UNIQUE NOT NULL,       
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,           
    dob DATE NULL,                         
    mother_name VARCHAR(100) NULL,         
    father_name VARCHAR(100) NULL,         
    blood_group VARCHAR(5) NULL,           
    city VARCHAR(50) NULL,                 
    aadhar_last_4 VARCHAR(50) NULL,         
    local_address VARCHAR(255) NULL,          
    hashed_pin VARCHAR(255) NOT NULL,      
    has_voted BOOLEAN DEFAULT FALSE NOT NULL,
    failed_attempts INT DEFAULT 0,         
    violation_count INT DEFAULT 0,         
    locked_status ENUM('ACTIVE', 'LOCKED', 'REVOKED') DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE SessionManagement (
    session_id CHAR(36) PRIMARY KEY,
    voter_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rapid_fire_timeout TIMESTAMP NOT NULL,  
    status ENUM('RAPID_FIRE', 'VOTING', 'EXPIRED', 'KILLED', 'COMPLETED') DEFAULT 'RAPID_FIRE',
    FOREIGN KEY (voter_id) REFERENCES VoterRegistry(voter_id)
);

CREATE TABLE CandidateRegistry (
    candidate_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    council VARCHAR(100)
);

CREATE TABLE VoteBox (
    vote_id INT AUTO_INCREMENT PRIMARY KEY,
    vote_token CHAR(36) UNIQUE NOT NULL,
    candidate_id INT NOT NULL,
    vote_hash VARCHAR(64) NOT NULL,
    session_id CHAR(36),
    FOREIGN KEY (session_id) REFERENCES SessionManagement(session_id),
    FOREIGN KEY (candidate_id) REFERENCES CandidateRegistry(candidate_id)
);

CREATE TABLE LoginAudit (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    voter_id INT,
    action VARCHAR(50), 
    details VARCHAR(255)
);

DELIMITER //
CREATE TRIGGER prevent_vote_update BEFORE UPDATE ON VoteBox
FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='SECURITY ALERT: Votes are immutable.'; //

CREATE TRIGGER prevent_vote_delete BEFORE DELETE ON VoteBox
FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='SECURITY ALERT: Votes are immutable and cannot be deleted.'; //

CREATE TRIGGER enforce_two_strike_rule BEFORE UPDATE ON VoterRegistry
FOR EACH ROW BEGIN
    IF NEW.failed_attempts >= 2 AND OLD.locked_status = 'ACTIVE' THEN
        SET NEW.locked_status = 'LOCKED';
    END IF;
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE sp_cast_vote(IN p_voter_id INT, IN p_candidate_id INT, IN p_session_id CHAR(36), IN p_vote_hash VARCHAR(64), IN p_receipt_token CHAR(36))
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Vote cast failed.'; END;
    START TRANSACTION;
    IF (SELECT has_voted FROM VoterRegistry WHERE voter_id = p_voter_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Double Voting Prevented.'; END IF;
    IF (SELECT locked_status FROM VoterRegistry WHERE voter_id = p_voter_id) != 'ACTIVE' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Account Locked.'; END IF;
    
    INSERT INTO VoteBox(vote_token, candidate_id, vote_hash, session_id) VALUES(p_receipt_token, p_candidate_id, p_vote_hash, p_session_id);
    UPDATE VoterRegistry SET has_voted = TRUE WHERE voter_id = p_voter_id;
    INSERT INTO LoginAudit(voter_id, action, details) VALUES(p_voter_id, 'VOTE_CAST', 'Vote securely recorded');
    UPDATE SessionManagement SET status = 'COMPLETED' WHERE session_id = p_session_id;
    COMMIT;
END //

CREATE PROCEDURE sp_revoke_voter(IN p_prn VARCHAR(20), IN p_reason VARCHAR(255))
BEGIN
    DECLARE v_voter_id INT;
    SELECT voter_id INTO v_voter_id FROM VoterRegistry WHERE prn = p_prn;
    UPDATE VoterRegistry SET locked_status = 'REVOKED', has_voted = TRUE WHERE voter_id = v_voter_id;
    UPDATE SessionManagement SET status = 'KILLED' WHERE voter_id = v_voter_id;
    INSERT INTO LoginAudit(voter_id, action, details) VALUES(v_voter_id, 'ADMIN_REVOKE', p_reason);
END //

CREATE PROCEDURE sp_reset_election()
BEGIN
    SET FOREIGN_KEY_CHECKS = 0;
    TRUNCATE TABLE VoteBox;
    TRUNCATE TABLE LoginAudit;
    TRUNCATE TABLE SessionManagement;
    DELETE FROM VoterRegistry;
    ALTER TABLE VoterRegistry AUTO_INCREMENT = 1;
    UPDATE ElectionState SET state = 'PENDING' WHERE id = 1;
    SET FOREIGN_KEY_CHECKS = 1;
END //

CREATE PROCEDURE sp_reset_candidates()
BEGIN
    SET FOREIGN_KEY_CHECKS = 0;
    TRUNCATE TABLE CandidateRegistry;
    SET FOREIGN_KEY_CHECKS = 1;
END //
DELIMITER ;

INSERT INTO CandidateRegistry (candidate_id, name, council) VALUES
(1, 'Raghav', 'Engineering'), (2, 'Yash', 'Science'), (3, 'Vinay', 'Management');

INSERT INTO VoterRegistry (prn, name, email, dob, mother_name, father_name, blood_group, city, aadhar_last_4, local_address, hashed_pin) VALUES
('1262241493', 'Hrushikesh Kapre', 'kaprehrushikeshwork@gmail.com', '2006-06-27', 'Pranjali', 'Praveen', NULL, 'Amravati', '6353', 'Kothrud, Pune', 'PENDING'),
('1262241494', 'Khushi ', 'kaprehrushikeshwork@gmail.com', '2006-10-07', NULL, 'Rajesh', 'B+', 'Pune', NULL , 'Shivajinagar', 'PENDING');


use authvote ;
select * from VoterRegistry;

select * from CandidateRegistry;

SELECT hashed_pin FROM VoterRegistry WHERE prn = '1262241493';

SELECT violation_count FROM VoterRegistry WHERE prn = '1262241493';

SELECT * FROM VoteBox;
