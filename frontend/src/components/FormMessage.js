import React from 'react';

const FormMessage = ({ error, success }) => {
  return (
    <div>
      {error && <p className="error-message">{error}</p>}
      {success && <p className="success-message">{success}</p>}
    </div>
  );
};

export default FormMessage;