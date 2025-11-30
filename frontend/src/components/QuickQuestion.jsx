import React, { useState } from 'react';
import api from '../services/api';

const SUGGESTED_QUESTIONS = [
  "What's our cash runway?",
  "How is ViiV tracking?",
  "What invoices need chasing?",
  "Can we afford to hire?",
  "What's our biggest risk?",
];

function QuickQuestion() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError(null);
    setAnswer(null);

    try {
      const data = await api.askQuestion(question);
      if (data.success) {
        setAnswer(data.answer);
      } else {
        setError(data.error || 'Failed to get answer');
      }
    } catch (err) {
      setError(err.message || 'Failed to get answer');
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setQuestion(suggestion);
    // Auto-submit
    setLoading(true);
    setError(null);
    setAnswer(null);

    api.askQuestion(suggestion)
      .then((data) => {
        if (data.success) {
          setAnswer(data.answer);
        } else {
          setError(data.error || 'Failed to get answer');
        }
      })
      .catch((err) => {
        setError(err.message || 'Failed to get answer');
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const formatAnswer = (text) => {
    if (!text) return null;

    return text.split('\n').map((line, index) => {
      if (line.startsWith('- ') || line.startsWith('* ')) {
        return <li key={index}>{line.slice(2)}</li>;
      }
      if (/^\d+\.\s/.test(line)) {
        return <li key={index}>{line.replace(/^\d+\.\s/, '')}</li>;
      }
      if (line.trim() === '') {
        return <br key={index} />;
      }
      return <p key={index}>{line}</p>;
    });
  };

  return (
    <div className="quick-question-panel">
      <div className="quick-question-header">
        <h2>Ask Your AI CFO</h2>
      </div>

      <form onSubmit={handleSubmit} className="quick-question-form">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a financial question..."
          disabled={loading}
        />
        <button type="submit" className="btn btn-primary" disabled={loading || !question.trim()}>
          {loading ? 'Thinking...' : 'Ask'}
        </button>
      </form>

      <div className="quick-question-suggestions">
        {SUGGESTED_QUESTIONS.map((suggestion, index) => (
          <button
            key={index}
            className="suggestion-btn"
            onClick={() => handleSuggestionClick(suggestion)}
            disabled={loading}
          >
            {suggestion}
          </button>
        ))}
      </div>

      {error && (
        <div className="quick-question-error">
          <p>{error}</p>
        </div>
      )}

      {answer && (
        <div className="quick-question-answer">
          <h4>Answer:</h4>
          <div className="answer-content">
            {formatAnswer(answer)}
          </div>
        </div>
      )}
    </div>
  );
}

export default QuickQuestion;
