import { useState, useEffect } from 'react';
import type { RefObject } from 'react';

function useOnScreen(ref: RefObject<HTMLElement>, rootMargin = '0px'): boolean {
  const [isIntersecting, setIntersecting] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        // Update our state when observer callback fires
        if (entry.isIntersecting) {
          setIntersecting(true);
          observer.unobserve(entry.target); // Stop observing once it's visible
        }
      },
      { rootMargin }
    );

    if (ref.current) observer.observe(ref.current);
    return () => { if (ref.current) observer.unobserve(ref.current) };
  }, [ref, rootMargin]);

  return isIntersecting;
}

export default useOnScreen;