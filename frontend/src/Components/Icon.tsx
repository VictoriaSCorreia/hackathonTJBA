import React, { useEffect, useRef } from 'react';
import feather from 'feather-icons';

interface IconProps {
  name: string;
  className?: string;
}

const Icon: React.FC<IconProps> = ({ name, className }) => {
  const iconRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (iconRef.current) {
      iconRef.current.innerHTML = (feather.icons as any)[name].toSvg({ class: className });
    }
  }, [name, className]);

  return <span ref={iconRef} />;
};

export default Icon;