import { useEffect } from 'react';
import feather from 'feather-icons';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  children: React.ReactNode;
  confirmText?: string;
  cancelText?: string;
}

const Modal: React.FC<ModalProps> = ({ isOpen, onClose, onConfirm, title, children, confirmText = "Confirm", cancelText = "Cancel" }) => {
  useEffect(() => {
    if (isOpen) {
      feather.replace();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-opacity-0 z-50 flex justify-center items-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl shadow-lg w-full max-w-md p-6 space-y-4 animate-fade-in-up"
        onClick={(e) => e.stopPropagation()} 
      >
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-bold text-gray-800">{title}</h2>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-gray-100 transition">
            <i data-feather="x" className="text-gray-600"></i>
          </button>
        </div>
        <div className="text-gray-600">
          {children}
        </div>
        <div className="flex justify-end space-x-4 pt-4">
          <button onClick={onClose} className="px-4 py-2 bg-gray-200 text-gray-800 font-medium rounded-lg hover:bg-gray-300 transition">
            {cancelText}
          </button>
          <button onClick={onConfirm} className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-500 transition">
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Modal;